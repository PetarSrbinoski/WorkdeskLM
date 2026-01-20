import re
from typing import Dict, List, Any

CITE_RE = re.compile(r"\[DOC=(.*?)\|PAGE=(\d+)\|CHUNK=(\d+)\]")


def extract_citations(answer: str) -> List[Dict[str, Any]]:
    out = []
    for m in CITE_RE.finditer(answer or ""):
        out.append({
            "doc_name": m.group(1),
            "page_number": int(m.group(2)),
            "chunk_index": int(m.group(3))
        })
    return out


def contains_any(answer: str, needles: List[str]) -> bool:
    a = (answer or "").lower()
    return any(n.lower() in a for n in needles)


def hit_at_k(retrieved: List[Dict[str, Any]], gold: List[Dict[str, Any]]) -> int:
    """
    retrieved items contain: doc_name, page_number, chunk_index
    gold: list of expected citations
    If gold empty, return 0 (not defined).
    """
    if not gold:
        return 0
    rset = {(r["doc_name"], r["page_number"], r["chunk_index"]) for r in retrieved}
    gset = {(g["doc_name"], g["page_number"], g["chunk_index"]) for g in gold}
    return 1 if len(rset.intersection(gset)) > 0 else 0


def citation_correct(pred_cites: List[Dict[str, Any]], gold: List[Dict[str, Any]]) -> int:
    if not gold:
        return 0
    pset = {(c["doc_name"], c["page_number"], c["chunk_index"]) for c in pred_cites}
    gset = {(g["doc_name"], g["page_number"], g["chunk_index"]) for g in gold}
    return 1 if len(pset.intersection(gset)) > 0 else 0
