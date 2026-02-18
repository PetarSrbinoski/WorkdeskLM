from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import settings
from app.core.ollama import pick_model as pick_ollama_model, generate as ollama_generate
from app.core.nvidia_llm import generate_chat as nvidia_generate


@dataclass(frozen=True)
class LLMResult:
    model: str
    response: str


async def pick_model(client: httpx.AsyncClient, mode: str) -> str:
    mode = mode or "fast"

    if settings.llm_provider == "nvidia":
        return settings.nvidia_quality_model

    return await pick_ollama_model(client, mode=mode)


async def generate(client: httpx.AsyncClient, mode: str, prompt: str) -> LLMResult:
    model = await pick_model(client, mode=mode)

    if settings.llm_provider == "nvidia":
        res = await nvidia_generate(client, model=model, prompt=prompt)
        return LLMResult(model=res.model, response=res.response)

    res = await ollama_generate(client, model=model, prompt=prompt)
    return LLMResult(model=res.model, response=res.response)
