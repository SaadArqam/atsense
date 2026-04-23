"""
LLM service using the official Groq Python client.

Responsibilities:
- Construct structured prompts for resume analysis.
- Call Groq API with retry logic.
- Parse and validate JSON responses.
- Extract LLM-refined skill lists.
- Generate improvement suggestions & section feedback.
"""

import os
import json
import logging
from typing import Dict, Any, List

from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration – all values come from environment variables, never hardcoded.
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "2048"))
TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.3"))  # low = more factual


def _get_client() -> Groq:
    """Initialise the Groq client (lazy, cached per-process)."""
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )
    return Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Core LLM call with basic retry
# ---------------------------------------------------------------------------
def _call_groq(system_prompt: str, user_prompt: str, retries: int = 2) -> str:
    """
    Send a chat completion request to Groq and return the raw text response.

    Args:
        system_prompt: System-level instruction.
        user_prompt: User message (contains resume + JD content).
        retries: How many times to retry on transient failures.

    Returns:
        Raw text content of the assistant's reply.
    """
    client = _get_client()

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning("Groq API call failed (attempt %d/%d): %s", attempt + 1, retries + 1, exc)
            if attempt == retries:
                raise

    return ""  # unreachable


def _extract_json(raw: str) -> Dict[str, Any]:
    """
    Robustly extract a JSON object from the LLM's raw response.
    Handles cases where the model wraps JSON in markdown code blocks.
    """
    # Strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last fence lines
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    # Find the first { and last } to extract JSON substring
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in LLM response: {raw[:300]}")

    json_str = cleaned[start:end]
    return json.loads(json_str)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
ANALYSIS_SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) and career coach AI.
Your task is to analyse a candidate's resume against a job description and produce STRICTLY structured JSON output.

Rules:
1. Be factual and specific — base all feedback on the actual resume text provided.
2. Do NOT hallucinate skills or experience that are not mentioned.
3. Output ONLY valid JSON — no markdown, no extra text, no commentary.
4. Keep suggestions actionable and concise (max 20 words each).
5. Section feedback should be 1–3 sentences per section.
"""

ANALYSIS_USER_PROMPT = """Analyse the resume against the job description below.

=== RESUME ===
{resume_text}

=== JOB DESCRIPTION ===
{jd_text}

Return EXACTLY this JSON structure (no other text):
{{
  "summary": "<2-3 sentence overall assessment>",
  "resume_skills": ["<skill1>", "<skill2>", "..."],
  "jd_skills": ["<skill1>", "<skill2>", "..."],
  "improvements": [
    "<actionable improvement 1>",
    "<actionable improvement 2>",
    "<actionable improvement 3>",
    "<actionable improvement 4>",
    "<actionable improvement 5>"
  ],
  "section_feedback": {{
    "summary": "<feedback on resume summary/objective section, or null if absent>",
    "experience": "<feedback on work experience section>",
    "skills": "<feedback on skills section>",
    "education": "<feedback on education section, or null if absent>",
    "projects": "<feedback on projects section, or null if absent>",
    "certifications": "<feedback on certifications, or null if absent>"
  }}
}}"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def analyze_with_llm(
    resume_text: str,
    jd_text: str,
    max_resume_chars: int = 6000,
    max_jd_chars: int = 3000,
) -> Dict[str, Any]:
    """
    Run the full LLM analysis and return a parsed, validated dict.

    Args:
        resume_text: Full extracted resume text.
        jd_text: Full job description text.
        max_resume_chars: Character limit to avoid exceeding context window.
        max_jd_chars: Character limit for JD.

    Returns:
        Parsed JSON dict with keys: summary, resume_skills, jd_skills,
        improvements, section_feedback.
    """
    # Truncate inputs to stay within context limits while preserving meaning
    truncated_resume = resume_text[:max_resume_chars]
    truncated_jd = jd_text[:max_jd_chars]

    user_prompt = ANALYSIS_USER_PROMPT.format(
        resume_text=truncated_resume,
        jd_text=truncated_jd,
    )

    logger.info("Calling Groq LLM (%s) for resume analysis...", GROQ_MODEL)
    raw_response = _call_groq(ANALYSIS_SYSTEM_PROMPT, user_prompt)
    logger.debug("LLM raw response length: %d chars", len(raw_response))

    parsed = _extract_json(raw_response)

    # Validate and fill missing keys with safe defaults
    defaults: Dict[str, Any] = {
        "summary": "Analysis complete.",
        "resume_skills": [],
        "jd_skills": [],
        "improvements": [],
        "section_feedback": {},
    }
    for key, default in defaults.items():
        if key not in parsed:
            logger.warning("LLM response missing key '%s', using default.", key)
            parsed[key] = default

    # Ensure lists are actually lists
    for list_key in ("resume_skills", "jd_skills", "improvements"):
        if not isinstance(parsed.get(list_key), list):
            parsed[list_key] = []

    if not isinstance(parsed.get("section_feedback"), dict):
        parsed["section_feedback"] = {}

    logger.info("LLM analysis successful.")
    return parsed


def extract_skills_with_llm(resume_text: str, jd_text: str) -> Dict[str, List[str]]:
    """
    Convenience wrapper: run LLM analysis and return only the skill lists.
    Used by the scorer for hybrid skill matching.
    """
    result = analyze_with_llm(resume_text, jd_text)
    return {
        "resume_skills": result.get("resume_skills", []),
        "jd_skills": result.get("jd_skills", []),
    }
