import requests
import time
import logging
from urllib.parse import quote
import feedparser

logging.basicConfig(level=logging.ERROR)

class ArxivClient:
    def __init__(self, delay=3.0):
        self.base_url = "http://export.arxiv.org/api/query"
        self.delay = delay
        self.last_request_time = 0
        print(f"DEBUG: ArxivClient initialized with delay={delay}")
    
    def search(self, query, start=0, max_results=100):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        print(f"DEBUG: Requesting arXiv with query={query}, start={start}, max_results={max_results}")
        response = requests.get(self.base_url, params=params)
        self.last_request_time = time.time()
        
        if response.status_code != 200:
            logging.error(f"ArXiv API error: {response.status_code} - {response.text}")
            raise Exception(f"ArXiv API error: {response.status_code}")
        
        print(f"DEBUG: ArXiv response received, length={len(response.text)}")
        
        feed = feedparser.parse(response.text)
        papers = []
        
        for entry in feed.entries:
            paper = {
                'arxiv_id': entry.id.split('/')[-1] if hasattr(entry, 'id') else None,
                'title': entry.title if hasattr(entry, 'title') else None,
                'abstract': entry.summary if hasattr(entry, 'summary') else None,
                'authors': [author.name for author in entry.authors] if hasattr(entry, 'authors') else [],
                'categories': [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else [],
                'pdf_url': next((link.href for link in entry.links if link.type == 'application/pdf'), None) if hasattr(entry, 'links') else None,
                'published_date': entry.published if hasattr(entry, 'published') else None
            }
            papers.append(paper)
        
        logging.info(f"Retrieved {len(papers)} papers from arXiv")
        return papers
