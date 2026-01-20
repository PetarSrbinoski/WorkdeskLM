from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List, Tuple

from sentence_transformers import CrossEncoder

from app.core.config import settings

logger = logging.getLogger("reranker")


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    logger.info("loading reranker model=%s", settings.rerank_model)
    # CPU is simplest and reliable inside Docker
    return CrossEncoder(settings.rerank_model, device="cpu")


def rerank(query: str, hits: List[Dict]) -> List[Dict]:
    """
    hits is list of Qdrant hit dicts with payload.text.
    Returns hits sorted by reranker score desc.
    Adds 'rerank_score' into each hit.
    """
    if not hits:
        return hits

    model = get_reranker()

    pairs: List[Tuple[str, str]] = []
    for h in hits:
        payload = h.get("payload") or {}
        text = str(payload.get("text", ""))
        pairs.append((query, text))

    scores = model.predict(pairs)

    for h, s in zip(hits, scores):
        h["rerank_score"] = float(s)

    hits_sorted = sorted(hits, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    return hits_sorted
