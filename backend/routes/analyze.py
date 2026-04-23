"""
FastAPI route: POST /analyze

Orchestrates the full pipeline:
  1. Parse PDF → clean text
  2. Compute ATS score (embedding + FAISS)
  3. LLM analysis (Groq)
  4. Hybrid skill extraction (regex + LLM)
  5. Return structured AnalysisResponse
"""

import logging
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status

from models.schemas import AnalysisResponse, SectionFeedback
from services.parser import parse_pdf
from services.scorer import compute_ats_score, extract_and_compare_skills
from services.llm import analyze_with_llm

logger = logging.getLogger(__name__)

router = APIRouter()

# Max upload size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyse a resume against a job description",
    description=(
        "Upload a PDF resume and paste a job description. "
        "Returns an ATS score, matched/missing skills, suggestions, and section feedback."
    ),
)
async def analyze_resume(
    resume: UploadFile = File(..., description="PDF resume file (max 10 MB)"),
    job_description: str = Form(..., min_length=50, description="Full job description text"),
) -> AnalysisResponse:
    """
    Full analysis pipeline endpoint.
    """
    # ── Guard: file type ──────────────────────────────────────────────────
    if resume.content_type not in ("application/pdf", "application/octet-stream"):
        if not (resume.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only PDF files are accepted.",
            )

    # ── Read file bytes ───────────────────────────────────────────────────
    file_bytes = await resume.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.",
        )

    # ── Step 1: PDF Parsing ───────────────────────────────────────────────
    try:
        parsed = parse_pdf(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    resume_text: str = parsed["full_text"]
    logger.info("Resume parsed: %d chars from %d pages.", len(resume_text), parsed["page_count"])

    # ── Step 2: Semantic ATS Scoring ──────────────────────────────────────
    try:
        scoring_result = compute_ats_score(resume_text, job_description)
    except Exception as exc:
        logger.error("Scoring failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring error: {exc}",
        )

    # ── Step 3: LLM Analysis via Groq ────────────────────────────────────
    try:
        llm_result = analyze_with_llm(resume_text, job_description)
    except EnvironmentError as exc:
        # Missing API key — surface clearly
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("LLM analysis failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM analysis error: {exc}",
        )

    # ── Step 4: Hybrid Skill Comparison ──────────────────────────────────
    llm_skills = {
        "resume_skills": llm_result.get("resume_skills", []),
        "jd_skills": llm_result.get("jd_skills", []),
    }
    skill_result = extract_and_compare_skills(resume_text, job_description, llm_skills)

    # ── Step 5: Assemble Response ─────────────────────────────────────────
    raw_section_fb = llm_result.get("section_feedback", {})
    section_feedback = SectionFeedback(
        summary=raw_section_fb.get("summary"),
        experience=raw_section_fb.get("experience"),
        skills=raw_section_fb.get("skills"),
        education=raw_section_fb.get("education"),
        projects=raw_section_fb.get("projects"),
        certifications=raw_section_fb.get("certifications"),
    )

    return AnalysisResponse(
        score=scoring_result["score"],
        matched_skills=skill_result["matched_skills"],
        missing_skills=skill_result["missing_skills"],
        suggestions=llm_result.get("improvements", []),
        section_feedback=section_feedback,
        top_matching_chunks=scoring_result.get("top_matching_chunks", []),
        semantic_gaps=scoring_result.get("semantic_gaps", []),
        llm_summary=llm_result.get("summary"),
    )
