from typing import List, Optional
from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=6, ge=1, le=20)
    min_score: float = Field(default=0.25, ge=0.0, le=1.0)
    doc_id: Optional[str] = None

class RetrievedChunk(BaseModel):
    chunk_id: str
    score: float
    doc_id: str
    doc_name: str
    page_number: int
    chunk_index: int
    text: str


class RetrieveResponse(BaseModel):
    question: str
    top_k: int
    min_score: float
    results: List[RetrievedChunk]