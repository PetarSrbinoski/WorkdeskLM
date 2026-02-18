from __future__ import annotations

import re
from typing import Tuple

from app.rag.prompt import ABSTAIN_TEXT


_CITATION_RE = re.compile(r"\[DOC=.*?\|PAGE=\d+\|CHUNK=\d+\]")


def should_abstain_from_retrieval(best_score: float, min_score: float) -> bool:
    return best_score < min_score


def validate_or_abstain(answer: str) -> Tuple[bool, str]:
    """
    Returns (abstained, final_answer).
    - If model outputs abstain text (exact), accept as abstention.
    - Otherwise require at least one valid citation tag.
    """
    ans = (answer or "").strip()
    if not ans:
        return True, ABSTAIN_TEXT

    if ans == ABSTAIN_TEXT:
        return True, ans

    if not _CITATION_RE.search(ans):
        return True, ABSTAIN_TEXT

    return False, ans
