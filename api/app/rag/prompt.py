from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ContextChunk:
    tag: str
    text: str


ABSTAIN_TEXT = "I don't know based on the provided documents."


def build_prompt(question: str, chunks: List[ContextChunk]) -> str:
    """
    Strict citation prompt. We enforce a specific tag format per chunk.
    The model must cite using the provided tags.
    """
    context_blocks = []
    for ch in chunks:
        context_blocks.append(f"{ch.tag}\n{ch.text}")

    context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(no context)"

    prompt = f"""You are a document-grounded assistant.

Rules you MUST follow:
1) Use ONLY the CONTEXT below. Do not use outside knowledge.
2) Every sentence in your answer MUST end with at least one citation tag exactly as provided, e.g. [DOC=...|PAGE=...|CHUNK=...]
3) If the answer is not supported by the context, respond with exactly:
{ABSTAIN_TEXT}
4) Do not invent citations. Only use the provided tags.
5) Keep the answer concise and factual.

QUESTION:
{question}

CONTEXT:
{context}

ANSWER:
"""
    return prompt
