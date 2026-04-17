from pydantic import BaseModel
from typing import Optional


class ParseRequest(BaseModel):
    pdf_url: str
    namespace: str = "default"


class QueryRequest(BaseModel):
    question: str
    project_id: Optional[str] = None
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    images: list[dict]


class Document(BaseModel):
    id: str
    name: str
    namespace: str
    page_count: int
    created_at: str
