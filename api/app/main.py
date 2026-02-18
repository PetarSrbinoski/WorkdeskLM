import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.time import utc_now_iso
from app.core.embeddings import embed_texts, embedding_dim
from app.core.qdrant import (
    ensure_collection,
    upsert_points,
    delete_points_by_doc_id,
    list_collections,
)
from app.core.qdrant import search as qdrant_search
from app.core.llm_router import generate as llm_generate, pick_model as llm_pick_model
from app.core.nvidia_llm import list_models as nvidia_list_models

from app.core.rerranker import rerank as rerank_hits  # Gen 3
from app.db.sqlite import connect, fetch_all, fetch_one, init_db, tx
from app.ingestion.chunking import chunk_text
from app.ingestion.parser import parse_file, sha256_bytes
from app.schemas.ingest import IngestResponse
from app.schemas.retrieve import RetrieveRequest, RetrieveResponse, RetrievedChunk
from app.schemas.chat import ChatRequest, ChatResponse, Citation, LatencyBreakdown
from app.rag.prompt import ContextChunk, build_prompt
from app.rag.guardrails import should_abstain_from_retrieval, validate_or_abstain
from app.rag.retrieval import run_retrieve_endpoint, run_chat_retrieval
from app.observability.otel import setup_otel

from app.memory.store import (
    create_session,
    get_session,
    add_message,
    list_messages,
    get_summary,
    upsert_summary,
)
from app.schemas.session import (
    CreateSessionRequest,
    CreateSessionResponse,
    GetSessionResponse,
    SessionMessage,
)
from app.schemas.studio import (
    BriefRequest,
    BriefResponse,
    FlashcardsRequest,
    FlashcardsResponse,
    Flashcard,
)
from app.studio.tools import retrieve_context, make_brief, make_flashcards

setup_logging(settings.log_level)
logger = logging.getLogger("api")

app = FastAPI(
    title="WorkdeskLM API",
    version="0.5.0",
    description="Gen 3: reranking, sessions/memory, studio tools.",
)

setup_otel(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = None




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

    return {
        "ok": ok,
        "url": tags_url,
        "models": models[:50],
        "expected": expected,
        "error": err,
    }

async def check_nvidia(client: httpx.AsyncClient) -> Dict[str, Any]:
    # OpenAI-compatible /models endpoint
    data = await nvidia_list_models(client)
    ok = bool(data.get("ok"))
    return {
        "ok": ok,
        "url": data.get("url"),
        "models": data.get("models", [])[:50],
        "expected": {
            "provider": "nvidia",
            "fast_model": settings.nvidia_fast_model,
            "quality_model": settings.nvidia_quality_model,
        },
        "error": data.get("error"),
    }


@app.on_event("startup")
async def _startup() -> None:
    global DB
    DB = connect(settings.sqlite_path)
    init_db(DB)
    logger.info("sqlite initialized path=%s", settings.sqlite_path)

    dim = embedding_dim()
    async with httpx.AsyncClient() as client:
        await ensure_collection(client, vector_size=dim)
    logger.info("qdrant collection ready name=%s dim=%s", settings.qdrant_collection, dim)


@app.get("/health")
async def health() -> JSONResponse:
    async with httpx.AsyncClient() as client:
        qdrant_task = check_qdrant(client)
        if settings.llm_provider.lower().strip() == "nvidia":
            llm_task = check_nvidia(client)
        else:
            llm_task = check_ollama(client)
        qdrant, llm = await asyncio.gather(qdrant_task, llm_task)

    status = "ok" if qdrant["ok"] and llm["ok"] else "degraded"
    payload = {
        "status": status,
        "env": settings.app_env,
        "services": {"qdrant": qdrant, "llm": llm},
        "embedding": {
            "model": settings.embedding_model,
            "dim": embedding_dim(),
            "collection": settings.qdrant_collection,
        },
        "gen3": {
            "enable_rerank": getattr(settings, "enable_rerank", True),
            "rerank_model": getattr(settings, "rerank_model", "unset"),
            "rerank_candidates": getattr(settings, "rerank_candidates", 20),
        },
    }
    code = 200 if status == "ok" else 503
    logger.info("health status=%s qdrant_ok=%s llm_ok=%s provider=%s", status, qdrant["ok"], llm["ok"], settings.llm_provider)
    return JSONResponse(content=payload, status_code=code)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "WorkdeskLM API is running. See /docs, /health, /ingest."}


@app.get("/qdrant/collections")
async def qdrant_collections() -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        return await list_collections(client)

@app.post("/sessions", response_model=CreateSessionResponse)
async def api_create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    sid = create_session(DB, req.title)
    return CreateSessionResponse(session_id=sid, title=req.title)


@app.get("/sessions/{session_id}", response_model=GetSessionResponse)
async def api_get_session(session_id: str) -> GetSessionResponse:
    s = get_session(DB, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = list_messages(DB, session_id, limit=50)
    summary = get_summary(DB, session_id)

    return GetSessionResponse(
        session_id=s["id"],
        title=s["title"],
        created_at=s["created_at"],
        summary=summary,
        messages=[SessionMessage(**m) for m in msgs],
    )


@app.post("/sessions/{session_id}/summarize")
async def api_summarize_session(session_id: str) -> Dict[str, Any]:
    s = get_session(DB, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = list_messages(DB, session_id, limit=50)
    transcript = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in msgs])[:12000]

    prompt = f"""Summarize this conversation for future context.
Keep it short (6-10 bullet points), factual, and focused on stable info.

TRANSCRIPT:
{transcript}

SUMMARY:
"""
    async with httpx.AsyncClient() as client:
        gen = await llm_generate(client, mode="fast", prompt=prompt)

    summary = gen.response.strip()
    upsert_summary(DB, session_id, summary)
    return {"session_id": session_id, "summary": summary}


# -----------------------------
# Gen 3: Studio Tools
# -----------------------------
@app.post("/studio/brief", response_model=BriefResponse)
async def api_brief(req: BriefRequest) -> BriefResponse:
    hits = await retrieve_context(req.question, top_n=20, doc_id=req.doc_id)
    brief = await make_brief(req.question, req.mode, hits)
    return BriefResponse(brief=brief)

@app.post("/studio/flashcards_debug")
async def api_flashcards_debug(req: FlashcardsRequest) -> Dict[str, Any]:
    hits = await retrieve_context("Create flashcards from this document.", top_n=20, doc_id=req.doc_id)

    # generate raw model output
    context = ""
    from app.studio.tools import _context_from_hits
    context = _context_from_hits(hits)

    prompt = f"""Create exactly {req.count} flashcards from the context below.
Return STRICT JSON with this format:
{{"cards":[{{"q":"...","a":"..."}}, ...]}}
Output JSON only.

CONTEXT:
{context}

JSON:
"""

    async with httpx.AsyncClient() as client:
        model = await llm_pick_model(client, mode=req.mode)
        gen = await llm_generate(client, model=model, prompt=prompt)

    return {
        "model_used": gen.model,
        "raw": gen.response,
        "context_preview": context[:1200]
    }

@app.post("/studio/flashcards", response_model=FlashcardsResponse)
async def api_flashcards(req: FlashcardsRequest) -> FlashcardsResponse:
    hits = await retrieve_context("Create flashcards from this document.", top_n=20, doc_id=req.doc_id)
    cards = await make_flashcards(req.count, req.mode, hits)
    return FlashcardsResponse(cards=[Flashcard(q=c["q"], a=c["a"]) for c in cards])


# -----------------------------
# Gen 1/2/3: Core endpoints
# -----------------------------
@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest) -> RetrieveResponse:
    """
    Embed question -> Qdrant vector search -> (Gen 3) optional rerank -> return chunks+scores.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty")

    enable_rerank = bool(getattr(settings, "enable_rerank", True))
    rerank_candidates = int(getattr(settings, "rerank_candidates", 20))

    mapped, _best, _timings = await run_retrieve_endpoint(
        question=question,
        top_k=req.top_k,
        min_score=req.min_score,
        doc_id=req.doc_id,
        enable_rerank=enable_rerank,
        rerank_candidates=rerank_candidates,
    )

    results = [RetrievedChunk(**row) for row in mapped]

    return RetrieveResponse(
        question=req.question,
        top_k=req.top_k,
        min_score=req.min_score,
        results=results,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Gen 3: RAG chat w/ strict citations + abstention + model switch (fast/quality),
    plus reranking and optional session memory.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty")

    t0 = time.perf_counter()

    # Optional: session memory context
    session_summary = None
    recent_msgs_txt = ""
    session_id = getattr(req, "session_id", None)  # backward compatible if schema not updated yet
    if session_id:
        s = get_session(DB, session_id)
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")
        session_summary = get_summary(DB, session_id)
        recent = list_messages(DB, session_id, limit=12)
        if recent:
            recent_msgs_txt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent])[:4000]    # Retrieve (embed -> qdrant -> optional rerank)
    enable_rerank = bool(getattr(settings, "enable_rerank", True))
    rerank_candidates = int(getattr(settings, "rerank_candidates", 20))

    citations, context_chunks, best_score, timings = await run_chat_retrieval(
        question=question,
        top_k=req.top_k,
        min_score=req.min_score,
        doc_id=req.doc_id,
        enable_rerank=enable_rerank,
        rerank_candidates=rerank_candidates,
    )

    embed_ms = timings.embed_ms
    qdrant_ms = timings.qdrant_ms

    # Abstain early if retrieval is weak
    if not context_chunks or should_abstain_from_retrieval(best_score, req.min_score):
        total_ms = int((time.perf_counter() - t0) * 1000)

        # Store messages if session_id provided
        if session_id:
            add_message(DB, session_id, "user", question)
            add_message(DB, session_id, "assistant", "I don't know based on the provided documents.")

        return ChatResponse(
            answer="I don't know based on the provided documents.",
            abstained=True,
            mode_used=req.mode,
            model_used="none",
            citations=[],
            latency=LatencyBreakdown(embed_ms=embed_ms, qdrant_ms=qdrant_ms, llm_ms=0, total_ms=total_ms),
        )

    # 3) Build prompt (with optional session memory)
    base_prompt = build_prompt(question=question, chunks=context_chunks)
    memory_block = ""
    if session_summary:
        memory_block += f"\n\nSESSION SUMMARY (for context, still must cite docs for claims):\n{session_summary}\n"
    if recent_msgs_txt:
        memory_block += f"\n\nRECENT CONVERSATION:\n{recent_msgs_txt}\n"

    prompt = base_prompt.replace("ANSWER:\n", f"{memory_block}\nANSWER:\n")    # 4) Generate (provider router: Ollama or NVIDIA)
    t_llm0 = time.perf_counter()
    async with httpx.AsyncClient() as client:
        try:
            gen = await llm_generate(client, mode=req.mode, prompt=prompt)
            answer_raw = gen.response
            model_used = gen.model
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"LLM generate failed: {str(e)}")

    llm_ms = int((time.perf_counter() - t_llm0) * 1000)

    # 5) Validate citations or abstain
    abstained, answer = validate_or_abstain(answer_raw)

    total_ms = int((time.perf_counter() - t0) * 1000)

    # Store messages if session_id provided
    if session_id:
        add_message(DB, session_id, "user", question)
        add_message(DB, session_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        abstained=abstained,
        mode_used=req.mode,
        model_used=model_used,
        citations=citations,
        latency=LatencyBreakdown(embed_ms=embed_ms, qdrant_ms=qdrant_ms, llm_ms=llm_ms, total_ms=total_ms),
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """
    Upload -> parse pages -> chunk -> store SQLite -> embed chunks -> upsert Qdrant.
    Dedupe by sha256.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    sha256 = sha256_bytes(raw)

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

    chunk_size = 1200
    overlap = 150

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

    texts = [r["text"] for r in chunk_rows]
    vectors = embed_texts(texts)
    if len(vectors) != len(chunk_rows):
        raise HTTPException(status_code=500, detail="Embedding count mismatch")

    points: List[Dict[str, Any]] = []
    for row, vec in zip(chunk_rows, vectors):
        points.append(
            {
                "id": row["id"],
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
    Delete document from SQLite + delete Qdrant vectors.
    """
    existing = fetch_one(DB, "SELECT id, name FROM documents WHERE id = ?", (doc_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")

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
