from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

class Paper:
    def __init__(self, paper_id: str = '', platform: str = 'arxiv', title: str = '', abstract: str = '', authors: List[str] = None, 
                 categories: List[str] = None, pdf_url: str = '', published_date: datetime = None, updated_date: datetime = None, arxiv_id: str = ''):
        self.paper_id = paper_id or arxiv_id
        self.platform = platform
        self.title = title
        self.abstract = abstract
        self.authors = authors or []
        self.categories = categories or []
        self.pdf_url = pdf_url
        self.published_date = published_date or datetime.now()
        self.updated_date = updated_date or datetime.now()
        
        # 하위 호환성
        self.arxiv_id = paper_id or arxiv_id
        
        logger.info(f"Paper created: {self.paper_id} - {self.title[:30]}...")
    
    def __str__(self):
        return f"Paper({self.paper_id}, {self.title[:30]}...)"
    
    def __repr__(self):
        return self.__str__()
