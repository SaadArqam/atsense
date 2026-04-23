"""
Embedding service using sentence-transformers (local model, no external API).

Architecture:
- Singleton SentenceTransformer instance (loaded once at startup)
- Chunked embedding for long documents
- FAISS index for fast vector search
- Cosine similarity helpers

Model: all-MiniLM-L6-v2 (384-dim, ~22 MB, CPU-friendly)
"""

import logging
import numpy as np
from functools import lru_cache
from typing import List, Tuple

import faiss
from sentence_transformers import SentenceTransformer

from utils.helpers import chunk_text

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384          # dimension of all-MiniLM-L6-v2
CHUNK_SIZE = 300             # words per chunk
CHUNK_OVERLAP = 50           # word overlap


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """
    Load the sentence-transformer model exactly once.
    lru_cache ensures the model is reused across requests (no repeated I/O).
    """
    logger.info("Loading SentenceTransformer model: %s", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Model loaded successfully.")
    return model


def embed_text(text: str) -> np.ndarray:
    """
    Embed a single string and return a 1-D float32 array.
    Used for whole-document similarity.
    """
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
    return embedding.astype(np.float32)


def embed_chunks(text: str) -> Tuple[List[str], np.ndarray]:
    """
    Split text into chunks, embed each, and return (chunks, embeddings matrix).

    Returns:
        chunks: List of text chunks.
        embeddings: np.ndarray of shape (n_chunks, EMBEDDING_DIM), float32, L2-normalised.
    """
    chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    if not chunks:
        raise ValueError("Text produced zero chunks after splitting.")

    model = _get_model()
    embeddings = model.encode(chunks, normalize_embeddings=True, convert_to_numpy=True, batch_size=32)
    return chunks, embeddings.astype(np.float32)


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build an in-memory FAISS IndexFlatIP (inner-product = cosine when L2-normalised).

    Args:
        embeddings: (n, dim) float32 array.

    Returns:
        Populated FAISS index.
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # inner product on unit vectors = cosine similarity
    index.add(embeddings)
    logger.debug("FAISS index built with %d vectors.", index.ntotal)
    return index


def query_index(
    index: faiss.Index,
    chunks: List[str],
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Search the FAISS index for the top-k most similar chunks.

    Args:
        index: Populated FAISS index.
        chunks: The text chunks corresponding to index rows.
        query_embedding: 1-D float32 array (already L2-normalised).
        top_k: How many results to return.

    Returns:
        List of (chunk_text, similarity_score) tuples, sorted by score desc.
    """
    query = query_embedding.reshape(1, -1)
    k = min(top_k, index.ntotal)
    scores, indices = index.search(query, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        results.append((chunks[idx], float(score)))

    return results


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two L2-normalised vectors.
    Since both vectors are already unit-length, dot product == cosine similarity.
    """
    return float(np.dot(vec_a, vec_b))
