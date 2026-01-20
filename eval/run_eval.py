import json
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import requests

from metrics import extract_citations, contains_any, hit_at_k, citation_correct

API_BASE = "http://localhost:8000"
DATASET = Path("eval/datasets/benchmark_v1.jsonl")
OUTDIR = Path("eval/results")


def load_dataset() -> List[Dict[str, Any]]:
    rows = []
    with DATASET.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def post_json(path: str, payload: Dict[str, Any], timeout=180) -> Dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def eval_mode(mode: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for ex in rows:
        q = ex["question"]
        answerable = bool(ex["answerable"])
        gold_contains = ex.get("gold_answer_contains", [])
        gold_cites = ex.get("gold_citations", [])

        # Retrieval
        ret = post_json("/retrieve", {
            "question": q,
            "top_k": 6,
            "min_score": 0.0,  # don't filter for hit@k measurement
        }, timeout=60)

        retrieved_norm = []
        for r in ret.get("results", []):
            retrieved_norm.append({
                "doc_name": r.get("doc_name", ""),
                "page_number": int(r.get("page_number", 0)),
                "chunk_index": int(r.get("chunk_index", 0)),
            })

        h1 = hit_at_k(retrieved_norm, gold_cites)

        # Chat
        t0 = time.perf_counter()
        chat = post_json("/chat", {
            "question": q,
            "mode": mode,
            "top_k": 6,
            "min_score": 0.25
        }, timeout=180)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        answer = chat.get("answer", "")
        abstained = bool(chat.get("abstained", False))
        cites = extract_citations(answer)

        cite_ok = citation_correct(cites, gold_cites)
        ans_ok = contains_any(answer, gold_contains) if answerable else False

        # For unanswerable questions
        abstain_ok = (abstained is True) if (answerable is False) else (abstained is False)

        results.append({
            "id": ex["id"],
            "mode": mode,
            "question": q,
            "answerable": answerable,
            "retrieval_hit@k": h1,
            "abstained": abstained,
            "abstain_correct": abstain_ok,
            "citation_correct": cite_ok,
            "answer_contains_gold": ans_ok,
            "latency_total_ms": chat.get("latency", {}).get("total_ms", elapsed_ms),
            "latency_embed_ms": chat.get("latency", {}).get("embed_ms", -1),
            "latency_qdrant_ms": chat.get("latency", {}).get("qdrant_ms", -1),
            "latency_llm_ms": chat.get("latency", {}).get("llm_ms", -1),
            "model_used": chat.get("model_used", ""),
        })
    return results


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(results)
    if n == 0:
        return {}
    def avg(key):
        return sum(float(r[key]) for r in results) / n

    return {
        "n": n,
        "retrieval_hit@k": avg("retrieval_hit@k"),
        "abstain_correct": avg("abstain_correct"),
        "citation_correct": avg("citation_correct"),
        "answer_contains_gold": avg("answer_contains_gold"),
        "latency_total_ms_avg": avg("latency_total_ms"),
    }


def write_csv(all_results: List[Dict[str, Any]], path: Path) -> None:
    if not all_results:
        return
    fieldnames = list(all_results[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_results)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    rows = load_dataset()

    all_results = []
    for mode in ["fast", "quality"]:
        r = eval_mode(mode, rows)
        all_results.extend(r)
        s = summarize(r)
        print(f"\n=== {mode.upper()} SUMMARY ===")
        for k, v in s.items():
            print(f"{k}: {v}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = OUTDIR / f"results_{ts}.csv"
    write_csv(all_results, out_csv)
    print(f"\nWrote: {out_csv}")


if __name__ == "__main__":
    main()
