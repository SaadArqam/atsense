"""
PDF parsing service using PyMuPDF (fitz).

Responsibilities:
- Open and iterate over PDF pages
- Extract raw text per page
- Normalize and clean the extracted text
- Return structured page-level and full-document text
"""

import logging
from typing import Dict, Any

import fitz  # PyMuPDF

from utils.helpers import normalize_text

logger = logging.getLogger(__name__)


def parse_pdf(file_bytes: bytes) -> Dict[str, Any]:
    """
    Parse a PDF from raw bytes and return normalized text.

    Args:
        file_bytes: Raw PDF file content.

    Returns:
        {
            "full_text": str,           # Entire resume as one string
            "pages": List[str],         # Per-page text
            "page_count": int,
        }

    Raises:
        ValueError: If the PDF is empty or unreadable.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        logger.error("Failed to open PDF: %s", exc)
        raise ValueError(f"Cannot open PDF: {exc}") from exc

    if doc.page_count == 0:
        raise ValueError("PDF has no pages.")

    pages: list[str] = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        raw = page.get_text("text")          # plain text extraction
        cleaned = normalize_text(raw)
        pages.append(cleaned)

    doc.close()

    full_text = "\n\n".join(p for p in pages if p)

    if not full_text.strip():
        raise ValueError("PDF appears to contain no extractable text (possibly scanned image).")

    logger.info("Parsed PDF: %d pages, %d chars", len(pages), len(full_text))

    return {
        "full_text": full_text,
        "pages": pages,
        "page_count": len(pages),
    }
