# WorkdeskLM — Local-First NotebookLM-Style RAG System

  WorkdeskLM is a fully local, document-grounded AI assistant inspired by Google’s NotebookLM.
  It runs entirely on a local machine (Windows + Docker + WSL2) and provides citation-grounded
  answers with strict abstention when information is missing.

  The project is designed as an internship-grade system with realistic infrastructure,
  clear evaluation hooks, and production-style observability planned in later generations.

  ---

  ## Key Features (Gen 1)

  • 100% local-first (no cloud dependencies)
  • PDF / TXT / Markdown ingestion
  • Page-aware chunking with overlap
  • Local embeddings (sentence-transformers)
  • Vector search with Qdrant
  • RAG chat with strict citations
  • “I don’t know” abstention guardrail
  • Runtime LLM switching:
      – Fast: phi3:mini
      – Quality: deepseek-r1-distill-qwen:7b (with fallbacks)
  • Modern UI (Next.js + Tailwind)
  • Docker Compose orchestration (Windows-friendly)

  ---

  ## Architecture Overview

  [ Architecture diagram image goes here ]

  WorkdeskLM is composed of three main services:

  • UI (Next.js + Tailwind)
      – Chat interface
      – Document upload
      – Model mode switch (Fast / Quality)
      – Source inspection panel

  • API (FastAPI)
      – Ingestion pipeline
      – Chunking + metadata storage
      – Embedding generation
      – Vector indexing & retrieval
      – RAG orchestration
      – Ollama integration
      – Guardrails & abstention logic

  • Vector Database (Qdrant)
      – Stores chunk embeddings
      – Enables semantic retrieval

  All services are orchestrated locally using Docker Compose.

  ---

  ## How RAG Works in WorkdeskLM

  1) A document is uploaded (PDF / TXT / MD)
  2) The document is parsed into pages
  3) Pages are chunked with overlap
  4) Each chunk is embedded locally
  5) Embeddings are stored in Qdrant
  6) When a question is asked:
     – The question is embedded
     – Top-K chunks are retrieved
     – If retrieval confidence is low → abstain
     – Otherwise, a prompt is built using only retrieved chunks
     – The LLM must cite each claim using document/page/chunk references

  If citations are missing or unsupported, the system responds with:

  “I don’t know based on the provided documents.”

  ---

  ## Local Models

  WorkdeskLM uses Ollama for local LLM execution:

  • Fast mode:
      – phi3:mini
      – Optimized for responsiveness

  • Quality mode:
      – qwen2.5:7b-instruct
      – Automatic fallback to:
          – llama3.1:8b-instruct

  Model selection happens at runtime via the UI.

  ---

  ## Running the Project (Windows)

  Requirements:
  • Windows 10/11
  • Docker Desktop with WSL2 enabled
  • Ollama installed on the host
  • NVIDIA GPU optional (used by Ollama, not required)

  Steps:

  1) Copy environment variables:
     cp .env.example .env

  2) Pull Ollama models:
     ollama pull phi3:mini
     ollama pull deepseek-r1-distill-qwen:7b

  3) Start all services:
     docker compose up -d --build

  4) Open:
     • UI: http://localhost:3000
     • API docs: http://localhost:8000/docs

  ---

  ## Generation Plan

  ### Gen 1 — Cited Document Chat (Current)
  • Local ingestion + RAG
  • Strict citations
  • Abstention guardrails
  • Next.js UI

  ### Gen 2 — Evaluation & Observability
  • Benchmark datasets
  • Retrieval & citation metrics
  • Latency analysis
  • OpenTelemetry + Prometheus + Grafana + Loki

  ### Gen 3 — Product-Grade Features
  • Reranking
  • Session memory & summaries
  • Web / YouTube ingestion
  • Study tools (briefs, flashcards, topic maps)

  ---

  ## Design Philosophy

  WorkdeskLM prioritizes:
  • Correctness over fluency
  • Explicit provenance over hallucination
  • Measurable improvements over demos
  • Local-first engineering

  This repository is intentionally structured to support iteration,
  evaluation, and extension.
