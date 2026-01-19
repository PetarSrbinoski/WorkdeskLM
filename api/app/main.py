import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.embeddings import embed_texts, embedding_dim
from app.core.qdrant import ensure_collection, upsert_points, delete_points_by_doc_id, list_collections
from app.db.sqlite import connect, fetch_all, fetch_one, init_db, tx
from app.ingestion.chunking import chunk_text
from app.ingestion.parser import parse_file, sha256_bytes
from app.schemas.ingest import IngestResponse

setup_logging(settings.log_level)
logger = logging.getLogger("api")

app = FastAPI(
    title="NotebookLM-Clone API (Gen 1)",
    version="0.4.0",
    description="Gen 1: Step 4: embeddings + Qdrant indexing.",
)

DB = None  # set on startup


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _check_http_json(
    client: httpx.AsyncClient, url: str, timeout_s: float = 2.0
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    try:
        resp = await client.get(url, timeout=timeout_s)
        resp.raise_for_status()
        data: Optional[Dict[str, Any]] = None
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text[:500]}
        return True, data, None
    except Exception as e:
        return False, None, str(e)


async def check_qdrant(client: httpx.AsyncClient) -> Dict[str, Any]:
    url = f"{settings.qdrant_url.rstrip('/')}/healthz"
    ok, data, err = await _check_http_json(client, url)
    return {"ok": ok, "url": url, "details": data, "error": err}


async def check_ollama(client: httpx.AsyncClient) -> Dict[str, Any]:
    base = settings.ollama_base_url.rstrip("/")
    tags_url = f"{base}/api/tags"
    ok, data, err = await _check_http_json(client, tags_url, timeout_s=3.0)

    models: List[str] = []
    if ok and data and isinstance(data, dict):
        raw_models = data.get("models", [])
        if isinstance(raw_models, list):
            for m in raw_models:
                if isinstance(m, dict) and "name" in m:
                    models.append(str(m["name"]))

    expected = {
        "fast_model": settings.fast_model,
        "quality_model": settings.quality_model,
        "fast_present": settings.fast_model in models if models else False,
        "quality_present": settings.quality_model in models if models else False,
    }

    return {"ok": ok, "url": tags_url, "models": models[:50], "expected": expected, "error": err}


@app.on_event("startup")
async def _startup() -> None:
    global DB
    DB = connect(settings.sqlite_path)
    init_db(DB)
    logger.info("sqlite initialized path=%s", settings.sqlite_path)

    # Ensure Qdrant collection exists (Step 4)
    dim = embedding_dim()
    async with httpx.AsyncClient() as client:
        await ensure_collection(client, vector_size=dim)
    logger.info("qdrant collection ready name=%s dim=%s", settings.qdrant_collection, dim)


@app.get("/health")
async def health() -> JSONResponse:
    async with httpx.AsyncClient() as client:
        qdrant_task = check_qdrant(client)
        ollama_task = check_ollama(client)
        qdrant, ollama = await asyncio.gather(qdrant_task, ollama_task)

    status = "ok" if qdrant["ok"] and ollama["ok"] else "degraded"
    payload = {
        "status": status,
        "env": settings.app_env,
        "services": {"qdrant": qdrant, "ollama": ollama},
        "embedding": {
            "model": settings.embedding_model,
            "dim": embedding_dim(),
            "collection": settings.qdrant_collection,
        },
    }
    code = 200 if status == "ok" else 503
    logger.info("health status=%s qdrant_ok=%s ollama_ok=%s", status, qdrant["ok"], ollama["ok"])
    return JSONResponse(content=payload, status_code=code)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "NotebookLM-Clone API is running. See /docs, /health, /ingest."}


@app.get("/qdrant/collections")
async def qdrant_collections() -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        return await list_collections(client)


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """
    Step 4: Upload -> parse pages -> chunk -> store SQLite -> embed chunks -> upsert Qdrant.
    Dedupe by sha256.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    sha256 = sha256_bytes(raw)

    # Dedupe check
    existing = fetch_one(DB, "SELECT * FROM documents WHERE sha256 = ?", (sha256,))
    if existing:
        cnt = fetch_one(DB, "SELECT COUNT(*) AS c FROM chunks WHERE doc_id = ?", (existing["id"],))
        chunk_count = int(cnt["c"]) if cnt and "c" in cnt else 0
        return IngestResponse(
            doc_id=existing["id"],
            name=existing["name"],
            mime_type=existing["mime_type"],
            size_bytes=existing["size_bytes"],
            sha256=existing["sha256"],
            page_count=existing["page_count"],
            chunk_count=chunk_count,
            deduped=True,
        )

    mime_type, pages = parse_file(file.filename, raw)
    page_count = len(pages)

    doc_id = str(uuid4())
    now = utc_now_iso()

    # Chunk defaults
    chunk_size = 900
    overlap = 150

    # Build chunk records in memory first so we can embed and upsert
    chunk_rows: List[Dict[str, Any]] = []
    for p in pages:
        chunks = chunk_text(p.text, chunk_size=chunk_size, overlap=overlap)
        for ch in chunks:
            chunk_rows.append(
                {
                    "id": str(uuid4()),
                    "doc_id": doc_id,
                    "page_number": p.page_number,
                    "chunk_index": ch.chunk_index,
                    "start_char": ch.start_char,
                    "end_char": ch.end_char,
                    "text": ch.text,
                    "created_at": now,
                }
            )

    total_chunks = len(chunk_rows)

    # Store SQLite (docs + pages + chunks)
    with tx(DB):
        DB.execute(
            """
            INSERT INTO documents (id, name, mime_type, sha256, size_bytes, page_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, file.filename, mime_type, sha256, len(raw), page_count, now),
        )

        for p in pages:
            DB.execute(
                """
                INSERT INTO pages (id, doc_id, page_number, text, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid4()), doc_id, p.page_number, p.text, now),
            )

        for row in chunk_rows:
            DB.execute(
                """
                INSERT INTO chunks (id, doc_id, page_number, chunk_index, start_char, end_char, text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["doc_id"],
                    row["page_number"],
                    row["chunk_index"],
                    row["start_char"],
                    row["end_char"],
                    row["text"],
                    row["created_at"],
                ),
            )

    # Embed + upsert to Qdrant
    texts = [r["text"] for r in chunk_rows]
    vectors = embed_texts(texts)
    if len(vectors) != len(chunk_rows):
        raise HTTPException(status_code=500, detail="Embedding count mismatch")

    points: List[Dict[str, Any]] = []
    for row, vec in zip(chunk_rows, vectors):
        points.append(
            {
                "id": row["id"],  # same as SQLite chunk id
                "vector": vec,
                "payload": {
                    "doc_id": doc_id,
                    "doc_name": file.filename,
                    "page_number": row["page_number"],
                    "chunk_index": row["chunk_index"],
                    "text": row["text"],
                },
            }
        )

    async with httpx.AsyncClient() as client:
        # Ensure collection exists (in case container restarted without startup hook)
        await ensure_collection(client, vector_size=embedding_dim())
        await upsert_points(client, points)

    logger.info(
        "ingested+indexed doc_id=%s name=%s pages=%s chunks=%s size=%s",
        doc_id,
        file.filename,
        page_count,
        total_chunks,
        len(raw),
    )

    return IngestResponse(
        doc_id=doc_id,
        name=file.filename,
        mime_type=mime_type,
        size_bytes=len(raw),
        sha256=sha256,
        page_count=page_count,
        chunk_count=total_chunks,
        deduped=False,
    )


@app.get("/documents")
async def list_documents() -> Dict[str, Any]:
    docs = fetch_all(
        DB,
        """
        SELECT
          d.id, d.name, d.mime_type, d.sha256, d.size_bytes, d.page_count, d.created_at,
          (SELECT COUNT(*) FROM chunks c WHERE c.doc_id = d.id) AS chunk_count
        FROM documents d
        ORDER BY d.created_at DESC
        """,
    )
    return {"count": len(docs), "documents": docs}


@app.get("/documents/{doc_id}/chunks")
async def list_chunks(doc_id: str, limit: int = 20, page: Optional[int] = None) -> Dict[str, Any]:
    existing = fetch_one(DB, "SELECT id, name, page_count FROM documents WHERE id = ?", (doc_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")

    limit = max(1, min(limit, 200))

    if page is not None:
        rows = fetch_all(
            DB,
            """
            SELECT id, doc_id, page_number, chunk_index, start_char, end_char, text, created_at
            FROM chunks
            WHERE doc_id = ? AND page_number = ?
            ORDER BY page_number ASC, chunk_index ASC
            LIMIT ?
            """,
            (doc_id, page, limit),
        )
    else:
        rows = fetch_all(
            DB,
            """
            SELECT id, doc_id, page_number, chunk_index, start_char, end_char, text, created_at
            FROM chunks
            WHERE doc_id = ?
            ORDER BY page_number ASC, chunk_index ASC
            LIMIT ?
            """,
            (doc_id, limit),
        )

    return {"doc": existing, "count": len(rows), "chunks": rows}


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> Dict[str, Any]:
    """
    Step 4: Delete document from SQLite + delete Qdrant vectors.
    """
    existing = fetch_one(DB, "SELECT id, name FROM documents WHERE id = ?", (doc_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete vectors first (best-effort). If Qdrant is down, don't leave SQLite deleted silently.
    async with httpx.AsyncClient() as client:
        try:
            await ensure_collection(client, vector_size=embedding_dim())
            await delete_points_by_doc_id(client, doc_id=doc_id)
        except Exception as e:
            logger.exception("qdrant delete failed doc_id=%s err=%s", doc_id, str(e))
            raise HTTPException(status_code=503, detail="Qdrant unavailable; aborting delete to keep consistency")

    with tx(DB):
        DB.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    logger.info("deleted doc_id=%s name=%s (sqlite + qdrant)", existing["id"], existing["name"])
    return {"deleted": True, "doc_id": doc_id}
