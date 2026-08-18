"""Semantic search over the `incidents` knowledge base (CockroachDB vector index)."""

from db import get_connection
from embeddings import embed_query, to_pgvector_literal


def search_similar_incidents(query: str, limit: int = 5) -> list[dict]:
    """Return past incidents ranked by cosine similarity to `query`.

    `distance` is in [0, 2] for cosine distance; lower means more similar.
    """
    vector = to_pgvector_literal(embed_query(query))

    conn = get_connection()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                substring(id::STRING, 1, 8) AS short_id,
                title,
                description,
                root_cause,
                resolution,
                severity,
                embedding <=> %s AS distance
            FROM incidents
            ORDER BY distance
            LIMIT %s
            """,
            (vector, limit),
        )
        columns = ["short_id", "title", "description", "root_cause", "resolution", "severity", "distance"]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()
