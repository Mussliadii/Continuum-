"""Embedding client for the Gemini API (gemini-embedding-001).

Vectors are requested at 768 dimensions to match the `incidents.embedding`
column (see backend/db/schema.sql) — Google's Matryoshka-trained embedding
model supports truncating to 768 dims with minimal quality loss, at a
quarter of the storage/index cost of the full 3072-dim vector.
"""

import os

import requests

EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-embedding-001:embedContent"
)
EMBEDDING_DIMENSIONS = 768


def _embed(text: str, task_type: str) -> list[float]:
    api_key = os.environ["GEMINI_API_KEY"]
    response = requests.post(
        EMBED_URL,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBEDDING_DIMENSIONS,
            "taskType": task_type,
        },
        timeout=30,
    )
    response.raise_for_status()
    # The embedContent endpoint returns a single "embedding" object, not a
    # plural "embeddings" list (that shape is only used by batchEmbedContents).
    return response.json()["embedding"]["values"]


def embed_document(text: str) -> list[float]:
    """Embed a past incident going INTO the knowledge base."""
    return _embed(text, "RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> list[float]:
    """Embed an incoming incident description used to SEARCH the knowledge base."""
    return _embed(text, "RETRIEVAL_QUERY")


def to_pgvector_literal(values: list[float]) -> str:
    """Format a Python float list as a CockroachDB VECTOR literal, e.g. '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"
