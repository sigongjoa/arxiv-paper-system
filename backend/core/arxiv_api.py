import requests
import time
import feedparser
import logging
from .config import RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)

class ArxivAPI:
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.last_request_time = 0
    
    def search(self, query, start=0, max_results=100):
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        response = requests.get(self.base_url, params=params)
        self.last_request_time = time.time()
        
        feed = feedparser.parse(response.text)
        papers = []
        
        for entry in feed.entries:
            paper = {
                'arxiv_id': entry.id.split('/')[-1],
                'title': entry.title,
                'abstract': entry.summary,
                'authors': ','.join([author.name for author in entry.authors]),
                'categories': ','.join([tag.term for tag in entry.tags]),
                'pdf_url': next((link.href for link in entry.links if link.type == 'application/pdf'), None),
                'published_date': entry.published
            }
            papers.append(paper)
        
        logger.info(f"Retrieved {len(papers)} papers from arXiv")
        return papers
