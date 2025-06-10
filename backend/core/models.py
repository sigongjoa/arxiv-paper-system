from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'

    paper_id = Column(String, primary_key=True, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)  # List of author names
    categories = Column(JSON, nullable=True) # List of category tags
    published_date = Column(DateTime, nullable=True)
    updated_date = Column(DateTime, nullable=True) # For tracking updates to papers
    
    def __repr__(self):
        return f"<Paper(paper_id='{self.paper_id}', title='{self.title[:50]}...')>"
