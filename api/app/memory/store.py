from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from app.db.sqlite import fetch_all, fetch_one, tx


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(conn, title: str) -> str:
    sid = str(uuid4())
    now = utc_now_iso()
    with tx(conn):
        conn.execute(
            "INSERT INTO sessions (id, title, created_at) VALUES (?, ?, ?)",
            (sid, title, now),
        )
    return sid


def get_session(conn, session_id: str) -> Optional[Dict[str, Any]]:
    return fetch_one(conn, "SELECT * FROM sessions WHERE id = ?", (session_id,))


def add_message(conn, session_id: str, role: str, content: str) -> str:
    mid = str(uuid4())
    now = utc_now_iso()
    with tx(conn):
        conn.execute(
            """
            INSERT INTO session_messages (id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (mid, session_id, role, content, now),
        )
    return mid


def list_messages(conn, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    limit = max(1, min(limit, 200))
    return fetch_all(
        conn,
        """
        SELECT id, role, content, created_at
        FROM session_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
        LIMIT ?
        """,
        (session_id, limit),
    )


def upsert_summary(conn, session_id: str, summary: str) -> None:
    now = utc_now_iso()
    with tx(conn):
        conn.execute(
            """
            INSERT INTO session_summaries (session_id, summary, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
              summary=excluded.summary,
              updated_at=excluded.updated_at
            """,
            (session_id, summary, now),
        )


def get_summary(conn, session_id: str) -> Optional[str]:
    row = fetch_one(conn, "SELECT summary FROM session_summaries WHERE session_id = ?", (session_id,))
    return str(row["summary"]) if row and "summary" in row else None
