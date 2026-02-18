from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.embeddings import embed_texts, embedding_dim
from app.core.qdrant import ensure_collection
from app.core.qdrant import search as qdrant_search
from app.core.rerranker import rerank as rerank_hits
from app.schemas.chat import Citation
from app.rag.prompt import ContextChunk


@dataclass(frozen=True)
class RetrievalTimings:
    embed_ms: int
    qdrant_ms: int


def _best_score(raw_hits: List[Dict[str, Any]]) -> float:
    best = 0.0
    for h in raw_hits or []:
        try:
            s = float(h.get("score", 0.0))
        except Exception:
            s = 0.0
        if s > best:
            best = s
    return best


def _map_for_retrieve(
    raw_hits: List[Dict[str, Any]], min_score: float
) -> List[Dict[str, Any]]:
    out = []
    for hit in raw_hits:
        score = float(hit.get("score", 0.0))
        if score < min_score:
            continue
        payload = hit.get("payload") or {}
        out.append(
            {
                "chunk_id": str(hit.get("id")),
                "score": float(score),
                "doc_id": str(payload.get("doc_id", "")),
                "doc_name": str(payload.get("doc_name", "")),
                "page_number": int(payload.get("page_number", 0) or 0),
                "chunk_index": int(payload.get("chunk_index", 0) or 0),
                "text": str(payload.get("text", "")),
            }
        )
    return out


def _map_for_chat(
    raw_hits: List[Dict[str, Any]], min_score: float
) -> Tuple[List[Citation], List[ContextChunk]]:
    citations: List[Citation] = []
    context_chunks: List[ContextChunk] = []

    for hit in raw_hits:
        score = float(hit.get("score", 0.0))
        if score < min_score:
            continue

        payload = hit.get("payload") or {}
        chunk_id = str(hit.get("id"))
        doc_id = str(payload.get("doc_id", ""))
        doc_name = str(payload.get("doc_name", ""))
        page_number = int(payload.get("page_number", 0) or 0)
        chunk_index = int(payload.get("chunk_index", 0) or 0)
        text = str(payload.get("text", ""))

        tag = f"[DOC={doc_name}|PAGE={page_number}|CHUNK={chunk_index}]"
        context_chunks.append(ContextChunk(tag=tag, text=text))

        citations.append(
            Citation(
                chunk_id=chunk_id,
                score=float(score),
                doc_id=doc_id,
                doc_name=doc_name,
                page_number=page_number,
                chunk_index=chunk_index,
                quote=text[:500],
            )
        )

    return citations, context_chunks


async def run_retrieval(
    question: str,
    top_k: int,
    min_score: float,
    doc_id: Optional[str] = None,
    enable_rerank: bool = True,
    rerank_candidates: int = 20,
) -> Tuple[List[Dict[str, Any]], float, RetrievalTimings]:
    """
    Embed question -> Qdrant vector search -> optional rerank -> truncate to top_k.

    Returns:
      raw_hits (possibly reranked, truncated to top_k),
      best_score among returned hits,
      timings (embed_ms, qdrant_ms)
    """
    # 1) Embed
    t_embed0 = time.perf_counter()
    qvec = embed_texts([question])[0]
    embed_ms = int((time.perf_counter() - t_embed0) * 1000)

    # 2) Retrieve
    t_q0 = time.perf_counter()
    fetch_n = int(rerank_candidates) if enable_rerank else int(top_k)

    async with httpx.AsyncClient() as client:
        await ensure_collection(client, vector_size=embedding_dim())
        raw_hits = await qdrant_search(
            client, query_vector=qvec, top_k=fetch_n, doc_id=doc_id
        )

    qdrant_ms = int((time.perf_counter() - t_q0) * 1000)

    # 3) Rerank
    if enable_rerank and len(raw_hits) > 1:
        raw_hits = rerank_hits(question, raw_hits)

    raw_hits = (raw_hits or [])[: int(top_k)]
    best = _best_score(raw_hits)

    return raw_hits, best, RetrievalTimings(embed_ms=embed_ms, qdrant_ms=qdrant_ms)


async def run_retrieve_endpoint(
    question: str,
    top_k: int,
    min_score: float,
    doc_id: Optional[str] = None,
    enable_rerank: bool = True,
    rerank_candidates: int = 20,
) -> Tuple[List[Dict[str, Any]], float, RetrievalTimings]:
    raw_hits, best, timings = await run_retrieval(
        question=question,
        top_k=top_k,
        min_score=min_score,
        doc_id=doc_id,
        enable_rerank=enable_rerank,
        rerank_candidates=rerank_candidates,
    )
    mapped = _map_for_retrieve(raw_hits, min_score=min_score)
    return mapped, best, timings


async def run_chat_retrieval(
    question: str,
    top_k: int,
    min_score: float,
    doc_id: Optional[str] = None,
    enable_rerank: bool = True,
    rerank_candidates: int = 20,
) -> Tuple[List[Citation], List[ContextChunk], float, RetrievalTimings]:
    raw_hits, best, timings = await run_retrieval(
        question=question,
        top_k=top_k,
        min_score=min_score,
        doc_id=doc_id,
        enable_rerank=enable_rerank,
        rerank_candidates=rerank_candidates,
    )
    citations, context_chunks = _map_for_chat(raw_hits, min_score=min_score)
    return citations, context_chunks, best, timings
