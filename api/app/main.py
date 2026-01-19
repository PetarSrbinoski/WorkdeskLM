import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.sqlite import connect, fetch_all, fetch_one, init_db, tx
from app.ingestion.parser import parse_file, sha256_bytes
from app.schemas.ingest import IngestResponse

setup_logging(settings.log_level)
logger = logging.getLogger("api")

app = FastAPI(
    title="NotebookLM-Clone API (Gen 1)",
    version="0.2.0",
    description="Gen 1: local-first cited doc chat. Step 2: ingest+parse+store.",
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
    }
    code = 200 if status == "ok" else 503
    logger.info("health status=%s qdrant_ok=%s ollama_ok=%s", status, qdrant["ok"], ollama["ok"])
    return JSONResponse(content=payload, status_code=code)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "NotebookLM-Clone API is running. See /docs, /health, /ingest."}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """
    Step 2: Upload a PDF/TXT/MD, parse into pages, store in SQLite.
    Dedupe by sha256.
    """
    if not file.filename:
        raise ValueError("Filename missing")

    raw = await file.read()
    if not raw:
        raise ValueError("Empty file")

    sha256 = sha256_bytes(raw)

    # Dedupe check
    existing = fetch_one(DB, "SELECT * FROM documents WHERE sha256 = ?", (sha256,))
    if existing:
        return IngestResponse(
            doc_id=existing["id"],
            name=existing["name"],
            mime_type=existing["mime_type"],
            size_bytes=existing["size_bytes"],
            sha256=existing["sha256"],
            page_count=existing["page_count"],
            deduped=True,
        )

    mime_type, pages = parse_file(file.filename, raw)
    page_count = len(pages)

    doc_id = str(uuid4())
    now = utc_now_iso()

    with tx(DB):
        DB.execute(
            """
            INSERT INTO documents (id, name, mime_type, sha256, size_bytes, page_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, file.filename, mime_type, sha256, len(raw), page_count, now),
        )

        for p in pages:
            page_id = str(uuid4())
            DB.execute(
                """
                INSERT INTO pages (id, doc_id, page_number, text, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (page_id, doc_id, p.page_number, p.text, now),
            )

    logger.info("ingested doc_id=%s name=%s pages=%s size=%s", doc_id, file.filename, page_count, len(raw))

    return IngestResponse(
        doc_id=doc_id,
        name=file.filename,
        mime_type=mime_type,
        size_bytes=len(raw),
        sha256=sha256,
        page_count=page_count,
        deduped=False,
    )


@app.get("/documents")
async def list_documents() -> Dict[str, Any]:
    docs = fetch_all(
        DB,
        """
        SELECT id, name, mime_type, sha256, size_bytes, page_count, created_at
        FROM documents
        ORDER BY created_at DESC
        """,
    )
    return {"count": len(docs), "documents": docs}

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> Dict[str, Any]:
    """
    Delete a document and all its pages (FK cascade).
    Step 4+: also delete vectors from Qdrant.
    """
    existing = fetch_one(DB, "SELECT id, name FROM documents WHERE id = ?", (doc_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")

    with tx(DB):
        DB.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    logger.info("deleted doc_id=%s name=%s", existing["id"], existing["name"])
    return {"deleted": True, "doc_id": doc_id}
