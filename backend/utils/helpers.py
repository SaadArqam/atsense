"""
General-purpose utility helpers.
Keep this module free of domain logic – pure utility functions only.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Clean and normalize raw extracted text.
    - Collapse multiple whitespace / newlines
    - Strip non-printable characters
    - Lowercase for downstream NLP
    """
    # Remove non-printable / control characters (keep newlines)
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    # Collapse runs of whitespace except newlines
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse runs of 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping word-based chunks for embedding.
    Overlap ensures semantic continuity at chunk boundaries.

    Args:
        text: The input string.
        chunk_size: Approximate words per chunk.
        overlap: Words shared between consecutive chunks.

    Returns:
        List of text chunks.
    """
    words = text.split()
    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # slide with overlap

    return chunks


def deduplicate(items: List[str]) -> List[str]:
    """Return list with duplicates removed, preserving order."""
    seen = set()
    result = []
    for item in items:
        key = item.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
