from typing import List, Optional
from pydantic import BaseModel, Field


class BriefRequest(BaseModel):
    doc_id: Optional[str] = None
    question: str = Field(default="Summarize the key points.", min_length=1, max_length=4000)
    mode: str = "quality"


class BriefResponse(BaseModel):
    brief: str


class FlashcardsRequest(BaseModel):
    doc_id: Optional[str] = None
    count: int = Field(default=8, ge=3, le=20)
    mode: str = "quality"


class Flashcard(BaseModel):
    q: str
    a: str


class FlashcardsResponse(BaseModel):
    cards: List[Flashcard]
