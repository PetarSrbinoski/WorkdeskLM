import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional


@dataclass(frozen=True)
class SqliteConfig:
    db_path: str


def ensure_parent_dir(db_path: str) -> None:
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def connect(db_path: str) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            sha256 TEXT NOT NULL UNIQUE,
            size_bytes INTEGER NOT NULL,
            page_count INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            start_char INTEGER NOT NULL,
            end_char INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pages_doc_page
        ON pages(doc_id, page_number);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_doc_page
        ON chunks(doc_id, page_number);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_doc_chunkindex
        ON chunks(doc_id, chunk_index);
        """
    )

    # --- Gen 3: sessions/memory ---
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_summaries (
            session_id TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_session_messages_sid
        ON session_messages(session_id, created_at);
        """
    )


    conn.commit()



@contextmanager
def tx(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def fetch_one(conn: sqlite3.Connection, sql: str, params: tuple) -> Optional[Dict[str, Any]]:
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    return dict(row) if row else None


def fetch_all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]
