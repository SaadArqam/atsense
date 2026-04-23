"""
Pydantic schemas for request and response validation.
Strict typing enforced throughout to prevent runtime surprises.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class AnalysisRequest(BaseModel):
    """Input model – job description string comes from form; PDF is uploaded separately."""
    job_description: str = Field(..., min_length=50, description="Full job description text")


class SectionFeedback(BaseModel):
    """Structured per-section feedback from LLM."""
    summary: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    projects: Optional[str] = None
    certifications: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Full analysis output returned to the client."""
    score: float = Field(..., ge=0, le=100, description="ATS compatibility score (0-100)")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    section_feedback: SectionFeedback = Field(default_factory=SectionFeedback)
    top_matching_chunks: List[str] = Field(default_factory=list)
    semantic_gaps: List[str] = Field(default_factory=list)
    llm_summary: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
