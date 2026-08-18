"""Transactional incident state — the agent's short-term memory.

`active_incidents` and `incident_events` hold the state of an incident while
it is being worked, so a chat session survives a page reload or a Lambda
cold start. `resolve_incident` closes the loop back into long-term memory:
the resolved incident is embedded and added to the `incidents` knowledge
base, so the agent's memory grows from what it just handled.
"""

from db import get_connection
from embeddings import embed_document, to_pgvector_literal


def create_incident(title: str, severity: str = "warning") -> str:
    conn = get_connection()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO active_incidents (title, status, severity) VALUES (%s, 'investigating', %s) RETURNING id",
            (title, severity),
        )
        return str(cur.fetchone()[0])
    finally:
        conn.close()


def get_active_incident(incident_id: str) -> dict | None:
    conn = get_connection()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, status, severity, opened_at, closed_at FROM active_incidents WHERE id = %s",
            (incident_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        columns = ["id", "title", "status", "severity", "opened_at", "closed_at"]
        return dict(zip(columns, row))
    finally:
        conn.close()


def log_event(incident_id: str, actor: str, event_type: str, content: str) -> None:
    conn = get_connection()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO incident_events (incident_id, actor, event_type, content) VALUES (%s, %s, %s, %s)",
            (incident_id, actor, event_type, content),
        )
    finally:
        conn.close()


def get_incident_events(incident_id: str) -> list[dict]:
    conn = get_connection()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            """
            SELECT actor, event_type, content, created_at
            FROM incident_events
            WHERE incident_id = %s
            ORDER BY created_at ASC
            """,
            (incident_id,),
        )
        columns = ["actor", "event_type", "content", "created_at"]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def resolve_incident(
    incident_id: str,
    description: str,
    root_cause: str,
    resolution: str,
    tags: list[str],
) -> None:
    """Close an active incident and fold it into the long-term knowledge base."""
    conn = get_connection()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT title, severity FROM active_incidents WHERE id = %s",
            (incident_id,),
        )
        title, severity = cur.fetchone()

        cur.execute(
            "UPDATE active_incidents SET status = 'resolved', closed_at = now() WHERE id = %s",
            (incident_id,),
        )

        embedding_text = f"{title}. {description} Tags: {', '.join(tags)}"
        vector = embed_document(embedding_text)
        cur.execute(
            """
            INSERT INTO incidents (title, description, root_cause, resolution, severity, tags, embedding, resolved_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            """,
            (title, description, root_cause, resolution, severity, tags, to_pgvector_literal(vector)),
        )
    finally:
        conn.close()
