from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from  app.core.config import settings
from  app.core.embeddings import embed_texts, embedding_dim
from  app.core.qdrant import ensure_collection, search as qdrant_search
from  app.core.ollama import pick_model, generate as ollama_generate


def _context_from_hits(hits: List[Dict[str, Any]], max_chars: int = 8000) -> str:
    parts = []
    total = 0
    for h in hits:
        payload = h.get("payload") or {}
        doc = payload.get("doc_name", "")
        page = payload.get("page_number", 0)
        chunk = payload.get("chunk_index", 0)
        text = str(payload.get("text", ""))
        block = f"[{doc} p{page} c{chunk}]\n{text}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n---\n\n".join(parts)


async def retrieve_context(
    question: str, top_n: int = 20, doc_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    qvec = embed_texts([question])[0]
    async with httpx.AsyncClient() as client:
        await ensure_collection(client, vector_size=embedding_dim())
        hits = await qdrant_search(
            client, query_vector=qvec, top_k=top_n, doc_id=doc_id
        )
    return hits


async def make_brief(question: str, mode: str, hits: List[Dict[str, Any]]) -> str:
    context = _context_from_hits(hits)
    prompt = f"""Create a clear, structured brief using ONLY the context below.
- Use short sections with headings.
- If the context is insufficient, say what is missing.

QUESTION:
{question}

CONTEXT:
{context}

BRIEF:
"""
    async with httpx.AsyncClient() as client:
        model = await pick_model(client, mode=mode)
        gen = await ollama_generate(client, model=model, prompt=prompt)
    return gen.response.strip()


async def make_flashcards(
    count: int, mode: str, hits: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    context = _context_from_hits(hits)
    prompt = f"""Create exactly {count} flashcards from the context below.
    Do NOT use markdown code fences.
Return STRICT JSON with this format:
{{"cards":[{{"q":"...","a":"..."}}, ...]}}

CONTEXT:
{context}

JSON:
"""
    async with httpx.AsyncClient() as client:
        model = await pick_model(client, mode=mode)
        gen = await ollama_generate(client, model=model, prompt=prompt)

    raw = (gen.response or "").strip()

    def strip_fences(s: str) -> str:
        if "```" not in s:
            return s
        lines = s.splitlines()
        out = []
        in_fence = False
        for line in lines:
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                out.append(line)
        return "\n".join(out).strip() or s

    def extract_json_object(s: str) -> str:
        s = strip_fences(s).strip()
        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return ""
        return s[start : end + 1].strip()

    json_str = extract_json_object(raw)
    if not json_str:
        return []

    try:
        data = json.loads(json_str)
        cards = data.get("cards", [])
        out = []
        for c in cards:
            if isinstance(c, dict) and "q" in c and "a" in c:
                q = str(c["q"]).strip()
                a = str(c["a"]).strip()
                if q and a:
                    out.append({"q": q, "a": a})
        return out[:count]
    except Exception:
        return []
