import requests
import time
import logging
from urllib.parse import quote

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
        return response.text
