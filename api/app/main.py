import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging

setup_logging(settings.log_level)
logger = logging.getLogger("api")


app = FastAPI(
    title="NotebookLM-Clone API",
    version="0.1.0",
    description="Gen 1: local-first cited doc chat. Step 0-1: infra + health checks.",
)


async def _check_http_json(
    client: httpx.AsyncClient, url: str, timeout_s: float = 2.0
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    try:
        resp = await client.get(url, timeout=timeout_s)
        resp.raise_for_status()
        # Some endpoints return non-json; handle safely
        data: Optional[Dict[str, Any]] = None
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text[:500]}
        return True, data, None
    except Exception as e:
        return False, None, str(e)


async def check_qdrant(client: httpx.AsyncClient) -> Dict[str, Any]:
    # Qdrant exposes /healthz
    url = f"{settings.qdrant_url.rstrip('/')}/healthz"
    ok, data, err = await _check_http_json(client, url)
    return {
        "ok": ok,
        "url": url,
        "details": data,
        "error": err,
    }


async def check_ollama(client: httpx.AsyncClient) -> Dict[str, Any]:
    base = settings.ollama_base_url.rstrip("/")
    tags_url = f"{base}/api/tags"
    ok, data, err = await _check_http_json(client, tags_url, timeout_s=3.0)

    models: List[str] = []
    if ok and data and isinstance(data, dict):
        # Ollama /api/tags returns {"models":[{"name":"..."}...]}
        raw_models = data.get("models", [])
        if isinstance(raw_models, list):
            for m in raw_models:
                if isinstance(m, dict) and "name" in m:
                    models.append(str(m["name"]))

    # Helpful “expected” flags for your two-mode setup
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


@app.get("/health")
async def health() -> JSONResponse:
    """
    Step 1 endpoint:
    - Confirms API is running
    - Confirms Qdrant is reachable
    - Confirms Ollama on Windows host is reachable
    """
    async with httpx.AsyncClient() as client:
        qdrant_task = check_qdrant(client)
        ollama_task = check_ollama(client)

        qdrant, ollama = await asyncio.gather(qdrant_task, ollama_task)

    status = "ok" if qdrant["ok"] and ollama["ok"] else "degraded"

    payload = {
        "status": status,
        "env": settings.app_env,
        "services": {
            "qdrant": qdrant,
            "ollama": ollama,
        },
    }

    code = 200 if status == "ok" else 503
    logger.info("health status=%s qdrant_ok=%s ollama_ok=%s", status, qdrant["ok"], ollama["ok"])
    return JSONResponse(content=payload, status_code=code)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "NotebookLM-Clone API is running. See /docs and /health."}
