from pydantic import BaseModel

class IngestResponse(BaseModel):
    doc_id: str
    name: str
    mime_type: str
    size_bytes: int
    sha256: str
    page_count: int
    chunk_count: int
    deduped: bool