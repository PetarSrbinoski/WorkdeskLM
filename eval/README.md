# WorkdeskLM – Evaluation 

This folder contains the evaluation setup I use to measure how well WorkdeskLM performs
beyond just “looking correct”.

The goal of Gen 2 is to understand *what works*, *what doesn’t*, and *why* — using
repeatable, local experiments.

---

## What is evaluated

I focus on the parts of a RAG system that usually fail silently:

  - Whether the correct document chunks are retrieved
  - Whether the model answers only when it should
  - Whether citations actually point to the right source
  - How long each request takes end-to-end

I run all evaluations locally against the running WorkdeskLM API.

---

## Dataset format

The benchmark dataset lives in:

  eval/datasets/benchmark_v1.jsonl

Each line is one evaluation example in JSON format.

Example:

  {
    "id": "q1",
    "doc_name": "policy.pdf",
    "question": "What is the refund window?",
    "answerable": true,
    "gold_answer_contains": ["30 days", "thirty days"],
    "gold_citations": [
      { "doc_name": "policy.pdf", "page_number": 2, "chunk_index": 1 }
    ]
  }

Notes:
  - answerable=false means the system should abstain
  - gold_answer_contains is used for lightweight answer checking
  - gold_citations are used to measure retrieval and citation accuracy

---

## Metrics tracked

  - retrieval_hit@k
      Did at least one correct chunk appear in the top-k retrieved results?

  - abstain_correct
      Did the system abstain when the question was unanswerable,
      and answer when it was answerable?

  - citation_correct
      Do the citations in the final answer match the expected document/page/chunk?

  - answer_contains_gold
      Does the answer contain at least one expected gold phrase?

  - latency (ms)
      Total latency, plus embed / retrieval / LLM breakdown

These metrics are intentionally simple and transparent.

---

## How to run the evaluation

  1) Start the full stack:
     `docker compose up -d --build`

  2) Make sure documents used in the benchmark are ingested via the ui

  3) Run:
     `python eval/run_eval.py`

The script will:
  - Query /retrieve and /chat endpoints
  - Evaluate both fast and quality modes
  - Print a summary to the console
  - Save a CSV file under eval/results/

---

## How I use the results

I use these results to:
  - Compare fast vs quality models
  - Identify retrieval bottlenecks
  - Measure hallucination control
  - Decide what to improve next (reranking, chunking, prompts)

