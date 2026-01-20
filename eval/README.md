# WorkdeskLM Evaluation (Gen 2)

## Dataset format
`eval/datasets/benchmark_v1.jsonl` is JSONL, one example per line.

Fields:
- id: unique id
- doc_name: expected doc (optional for unanswerable)
- question: evaluation question
- answerable: true/false
- gold_answer_contains: list of acceptable substrings
- gold_citations: list of {doc_name, page_number, chunk_index}

## Run
1) Start stack: `docker compose up -d --build`
2) Run eval:
   - `python eval/run_eval.py`
Outputs CSV under `eval/results/`.
