from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    chunk_index: int
    start_char: int
    end_char: int
    text: str


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = (text or "").replace("\x00", " ")
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    text = normalize_text(text)
    if not text:
        return []

    step = chunk_size - overlap
    n = len(text)

    chunks: List[Chunk] = []
    start = 0
    chunk_index = 0

    while start < n:
        end = min(start + chunk_size, n)
        chunk_str = text[start:end].strip()
        if chunk_str:
            chunks.append(
                Chunk(
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    text=chunk_str,
                )
            )
            chunk_index += 1

        if end >= n:
            break
        start += step

    return chunks
