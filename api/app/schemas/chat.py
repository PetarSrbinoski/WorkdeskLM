from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    mode: str = Field(default="fast")  # fast or quality
    top_k: int = Field(default=6, ge=1, le=20)
    min_score: float = Field(default=0.25, ge=0.0, le=1.0)
    doc_id: Optional[str] = None


class Citation(BaseModel):
    chunk_id: str
    score: float
    doc_id: str
    doc_name: str
    page_number: int
    chunk_index: int
    quote: str


class LatencyBreakdown(BaseModel):
    embed_ms: int
    qdrant_ms: int
    llm_ms: int
    total_ms: int


class ChatResponse(BaseModel):
    answer: str
    abstained: bool
    mode_used: str
    model_used: str
    citations: List[Citation]
    latency: LatencyBreakdown
