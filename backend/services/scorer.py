"""
ATS Scoring & Skill Extraction service.

Responsibilities:
1. Compute semantic (cosine) ATS score between resume and JD embeddings.
2. Find top matching chunks via FAISS search.
3. Identify semantic gaps (JD chunks not well-covered by resume).
4. Hybrid skill extraction: regex/keyword list + LLM refinement.
"""

import re
import logging
from typing import Dict, List, Tuple, Any

import numpy as np

from services.embedding import (
    embed_text,
    embed_chunks,
    build_faiss_index,
    query_index,
    cosine_similarity,
)
from utils.helpers import deduplicate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated tech skill vocabulary (used for fast regex-based extraction)
# Extend this list freely — it's the "seed" vocabulary before LLM refinement.
# ---------------------------------------------------------------------------
COMMON_SKILLS: List[str] = [
    # Programming Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "Kotlin", "Swift", "Ruby", "PHP", "Scala", "R", "MATLAB", "Bash",
    # Web / Frontend
    "React", "Next.js", "Vue", "Angular", "HTML", "CSS", "Tailwind",
    "Redux", "GraphQL", "REST", "Webpack", "Vite",
    # Backend / Frameworks
    "FastAPI", "Django", "Flask", "Spring Boot", "Express", "Node.js",
    "NestJS", "Laravel",
    # Data / ML / AI
    "TensorFlow", "PyTorch", "scikit-learn", "Keras", "XGBoost", "LightGBM",
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "Hugging Face",
    "LangChain", "LlamaIndex", "OpenAI", "Groq", "FAISS", "Pinecone",
    "sentence-transformers", "BERT", "GPT", "LLM", "NLP",
    # Databases
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Cassandra",
    "Elasticsearch", "DynamoDB", "Supabase", "Firebase",
    # Cloud / DevOps
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "Ansible",
    "CI/CD", "GitHub Actions", "Jenkins", "Prometheus", "Grafana",
    # Data Engineering
    "Spark", "Kafka", "Airflow", "dbt", "Snowflake", "BigQuery", "Redshift",
    # Other
    "Git", "Linux", "Agile", "Scrum", "JIRA", "Figma",
    "Microservices", "System Design", "API Design",
]


def _build_skill_pattern(skills: List[str]) -> re.Pattern:
    """
    Build a compiled regex that matches any skill from the list,
    case-insensitively, at word boundaries.
    """
    escaped = [re.escape(s) for s in sorted(skills, key=len, reverse=True)]
    pattern = r"\b(" + "|".join(escaped) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


_SKILL_PATTERN = _build_skill_pattern(COMMON_SKILLS)


def extract_skills_regex(text: str) -> List[str]:
    """
    Extract skills from text using the compiled regex pattern.
    Returns a deduplicated, title-cased list.
    """
    raw_matches = _SKILL_PATTERN.findall(text)
    # Normalise: use title-case version from COMMON_SKILLS vocab
    skill_map = {s.lower(): s for s in COMMON_SKILLS}
    skills = [skill_map.get(m.lower(), m) for m in raw_matches]
    return deduplicate(skills)


def compute_ats_score(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Full ATS scoring pipeline:

    1. Embed full documents → cosine similarity → base score.
    2. Build FAISS index over resume chunks.
    3. Query with JD chunks → top matching passages.
    4. Detect semantic gaps: JD chunks with low similarity.

    Returns rich dict consumed by the route handler.
    """
    logger.info("Computing ATS score...")

    # ── Step 1: Document-level cosine similarity ──────────────────────────
    resume_emb = embed_text(resume_text)
    jd_emb = embed_text(jd_text)
    doc_similarity = cosine_similarity(resume_emb, jd_emb)

    # ── Step 2: Chunk resume & build FAISS index ──────────────────────────
    resume_chunks, resume_chunk_embs = embed_chunks(resume_text)
    faiss_index = build_faiss_index(resume_chunk_embs)

    # ── Step 3: Query with JD embedding → top matching chunks ─────────────
    top_matches: List[Tuple[str, float]] = query_index(
        faiss_index, resume_chunks, jd_emb, top_k=5
    )

    # ── Step 4: Identify semantic gaps ───────────────────────────────────
    jd_chunks, jd_chunk_embs = embed_chunks(jd_text)
    semantic_gaps: List[str] = []

    for jd_chunk, jd_c_emb in zip(jd_chunks, jd_chunk_embs):
        # Find best-matching resume chunk for this JD chunk
        results = query_index(faiss_index, resume_chunks, jd_c_emb, top_k=1)
        if results:
            best_score = results[0][1]
            # Threshold: chunks with similarity < 0.35 are "gaps"
            if best_score < 0.35:
                gap_snippet = jd_chunk[:120].strip()
                if gap_snippet and len(gap_snippet) > 20:
                    semantic_gaps.append(gap_snippet)

    semantic_gaps = deduplicate(semantic_gaps)[:5]  # top 5 gaps

    # ── Step 5: Scale similarity to 0–100 ATS score ──────────────────────
    # Cosine similarity for normalised vectors is in [-1, 1].
    # We clamp to [0, 1] then scale to [0, 100].
    raw_score = max(0.0, min(1.0, doc_similarity))

    # Apply a mild power curve so mid-range resumes don't cluster near 50.
    ats_score = round((raw_score ** 0.75) * 100, 1)

    logger.info(
        "ATS score: %.1f (raw cosine: %.4f, gaps: %d)",
        ats_score, doc_similarity, len(semantic_gaps)
    )

    return {
        "score": ats_score,
        "raw_cosine": round(doc_similarity, 4),
        "top_matching_chunks": [chunk for chunk, _ in top_matches],
        "semantic_gaps": semantic_gaps,
    }


def extract_and_compare_skills(
    resume_text: str,
    jd_text: str,
    llm_skills: Dict[str, List[str]] | None = None,
) -> Dict[str, List[str]]:
    """
    Hybrid skill comparison:
    - Base: regex extraction from both texts.
    - Refinement: if llm_skills are provided, merge and deduplicate.

    Args:
        resume_text: Full resume text.
        jd_text: Full job description text.
        llm_skills: Optional {"resume_skills": [...], "jd_skills": [...]} from LLM.

    Returns:
        {"matched_skills": [...], "missing_skills": [...]}
    """
    # Regex-based extraction
    regex_resume_skills = set(s.lower() for s in extract_skills_regex(resume_text))
    regex_jd_skills = set(s.lower() for s in extract_skills_regex(jd_text))

    # Merge with LLM-extracted skills if provided
    if llm_skills:
        llm_resume = set(s.lower() for s in llm_skills.get("resume_skills", []))
        llm_jd = set(s.lower() for s in llm_skills.get("jd_skills", []))
        all_resume_skills = regex_resume_skills | llm_resume
        all_jd_skills = regex_jd_skills | llm_jd
    else:
        all_resume_skills = regex_resume_skills
        all_jd_skills = regex_jd_skills

    matched = sorted(all_resume_skills & all_jd_skills)
    missing = sorted(all_jd_skills - all_resume_skills)

    return {
        "matched_skills": [s.title() for s in matched],
        "missing_skills": [s.title() for s in missing],
    }
