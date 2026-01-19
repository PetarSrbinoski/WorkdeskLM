from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("ollama")


@dataclass(frozen=True)
class OllamaGenerateResult:
    model: str
    response: str


async def list_models(client: httpx.AsyncClient) -> List[str]:
    """
    Returns list of model names Ollama.
    """
    base = settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/tags"
    r = await client.get(url, timeout=10.0)
    r.raise_for_status()
    data = r.json()
    models: List[str] = []
    for m in data.get("models", []) or []:
        if isinstance(m, dict) and "name" in m:
            models.append(str(m["name"]))
    return models


def _quality_candidates() -> List[str]:
    primary = settings.quality_model
    fallbacks = [m.strip() for m in settings.quality_fallback_models.split(",") if m.strip()]

    seen = set()
    out: List[str] = []
    for m in [primary] + fallbacks:
        if m not in seen:
            out.append(m)
            seen.add(m)
    return out


async def pick_model(client: httpx.AsyncClient, mode: str) -> str:
    """
    Pick an Ollama model name based on mode and availability.
    mode: "fast" | "quality"
    """
    mode = (mode or "fast").lower().strip()
    available = []
    try:
        available = await list_models(client)
    except Exception:
        available = []

    if mode == "fast":
        return settings.fast_model

    # quality
    candidates = _quality_candidates()
    if available:
        for c in candidates:
            if c in available:
                return c
    return candidates[0]


async def generate(
        client: httpx.AsyncClient, model: str, prompt: str,
        timeout_s: Optional[float] = None, ) -> OllamaGenerateResult:
    """
    Calls /api/generate with stream=false.
    """
    base = settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/generate"
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    t = timeout_s if timeout_s is not None else settings.ollama_timeout_s
    r = await client.post(url, json=payload, timeout=t)
    r.raise_for_status()
    data = r.json()
    return OllamaGenerateResult(model=model, response=str(data.get("response", "")).strip())
