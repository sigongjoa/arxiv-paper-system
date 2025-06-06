from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PaperResponse(BaseModel):
    id: int
    arxiv_id: str
    platform: str
    title: str
    abstract: Optional[str]
    authors: str
    categories: str
    pdf_url: Optional[str]
    published_date: Optional[datetime]
    structured_summary: Optional[str]
    created_at: Optional[datetime]
    crawled: Optional[str]

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    max_results: int = 10

class PaginatedResponse(BaseModel):
    items: List[PaperResponse]
    total: int
    page: int
    pages: int
