from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("qdrant")


def _collection_url() -> str:
    return f"{settings.qdrant_url.rstrip('/')}/collections/{settings.qdrant_collection}"


async def ensure_collection(client: httpx.AsyncClient, vector_size: int) -> None:
    """
    Create the collection if it doesn't exist.
    If it exists, do nothing.
    """
    url = _collection_url()

    r = await client.get(url, timeout=5.0)
    if r.status_code == 200:
        return
    if r.status_code != 404:
        r.raise_for_status()

    payload = {
        "vectors": {
            "size": vector_size,
            "distance": "Cosine",
        }
    }
    logger.info("creating qdrant collection name=%s dim=%s", settings.qdrant_collection, vector_size)
    cr = await client.put(url, json=payload, timeout=10.0)
    cr.raise_for_status()


async def upsert_points(client: httpx.AsyncClient, points: List[Dict[str, Any]] ) -> None:
    """
    Bulk upsert points.
    {id, vector, payload}
    """
    if not points:
        return
    url = f"{_collection_url()}/points?wait=true"
    r = await client.put(url, json={"points": points}, timeout=60.0)
    r.raise_for_status()


async def delete_points_by_doc_id(client: httpx.AsyncClient, doc_id: str) -> int:
    """
    Delete all points matching payload.doc_id == doc_id.
    Returns how many were deleted if Qdrant reports it (best-effort).
    """
    url = f"{_collection_url()}/points/delete?wait=true"
    payload = {
        "filter": {
            "must": [
                {"key": "doc_id", "match": {"value": doc_id}}
            ]
        }
    }
    r = await client.post(url, json=payload, timeout=60.0)
    r.raise_for_status()
    data = r.json()
    return int(data.get("result", {}).get("operation_id", 0))  # not actual count, indicates success


async def list_collections(client: httpx.AsyncClient) -> Dict[str, Any]:
    url = f"{settings.qdrant_url.rstrip('/')}/collections"
    r = await client.get(url, timeout=5.0)
    r.raise_for_status()
    return r.json()
