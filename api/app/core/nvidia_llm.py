from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger("nvidia_llm")


@dataclass(frozen=True)
class NvidiaGenResult:
    model: str
    response: str


async def generate_chat(
    client: httpx.AsyncClient,
    model: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 4200,
) -> NvidiaGenResult:
    base = settings.nvidia_base_url.rstrip("/")
    url = f"{base}/chat/completions"

    api_key = settings.nvidia_api_key or ""

    if not api_key.strip():
        raise RuntimeError("No nvidia api key set. Set it in the env file")

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    t = 300
    r = await client.post(url, headers=headers, json=payload, timeout=t)
    r.raise_for_status()
    data = r.json()

    try:
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    except Exception:
        content = ""

    return NvidiaGenResult(model=model, response=str(content).strip())


async def list_models(
    client: httpx.AsyncClient, timeout_s: float = 10.0
) -> Dict[str, Any]:
    """Best-effort model listing from {base}/models (OpenAI-compatible)."""
    base = settings.nvidia_base_url.rstrip("/")
    url = f"{base}/models"

    api_key = settings.nvidia_api_key or ""
    if not api_key.strip():
        return {
            "ok": False,
            "url": url,
            "error": "Missing NVIDIA_API_KEY",
            "models": [],
        }

    headers = {"Authorization": f"Bearer {api_key.strip()}"}

    try:
        r = await client.get(url, headers=headers, timeout=timeout_s)
        r.raise_for_status()
        data = r.json()
        models = []
        for m in data.get("data", []) or []:
            mid = m.get("id")
            if mid:
                models.append(str(mid))
        return {"ok": True, "url": url, "error": None, "models": models[:50]}
    except Exception as e:
        return {"ok": False, "url": url, "error": str(e), "models": []}
