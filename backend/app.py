"""
FastAPI application entry point.

- Configures logging
- Registers routers
- Adds CORS middleware (Streamlit runs on a different port)
- Exposes health-check endpoint
- Triggers model pre-load on startup to warm up sentence-transformer
"""

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.analyze import router as analyze_router
from models.schemas import HealthResponse

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("app")


# ---------------------------------------------------------------------------
# Lifespan: warm-up the sentence-transformer model on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Pre-load the embedding model at startup so the first request is not slow.
    Model is cached via lru_cache in embedding.py.
    """
    logger.info("Starting up – pre-loading embedding model...")
    try:
        from services.embedding import _get_model
        _get_model()  # triggers download + cache on first run
        logger.info("Embedding model ready.")
    except Exception as exc:
        logger.warning("Could not pre-load model: %s", exc)
    yield
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Resume Analyzer & ATS Scorer",
    description=(
        "Upload a PDF resume and job description to get an ATS score, "
        "skill gap analysis, and LLM-powered improvement suggestions."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS – allow Streamlit frontend (default port 8501) and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Simple liveness probe."""
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Resume Analyzer API",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Dev-mode entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
