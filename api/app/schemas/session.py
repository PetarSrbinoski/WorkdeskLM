from typing import List, Optional
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str = Field(default="New session", min_length=1, max_length=120)


class CreateSessionResponse(BaseModel):
    session_id: str
    title: str


class SessionMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class GetSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    summary: Optional[str]
    messages: List[SessionMessage]
