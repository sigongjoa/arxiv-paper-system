from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Optional
import logging
from pydantic import Field

logger = logging.getLogger(__name__)

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'

    paper_id = Column(String, primary_key=True, unique=True, nullable=False)
    external_id = Column(String, index=True, nullable=True) # arXiv ID 등 외부 플랫폼 ID
    platform = Column(String, index=True, default="arxiv", nullable=True) # "arxiv", "rss" 등
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)  # List of author names
    categories = Column(JSON, nullable=True) # List of category tags
    pdf_url = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True) # 임베딩 필드 추가
    published_date = Column(DateTime, nullable=True)
    updated_date = Column(DateTime, nullable=True) # For tracking updates to papers
    
    def __repr__(self):
        return f"<Paper(paper_id='{self.paper_id}', title='{self.title[:50]}...')>"
