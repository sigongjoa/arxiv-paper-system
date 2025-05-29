from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Paper:
    arxiv_id: str
    title: str
    abstract: str
    authors: List[str]
    categories: List[str]
    pdf_url: str
    published_date: datetime
    updated_date: datetime
    
    def __post_init__(self):
        print(f"DEBUG: Created paper {self.arxiv_id} - {self.title[:50]}...")
