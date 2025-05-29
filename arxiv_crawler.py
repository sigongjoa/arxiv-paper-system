import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta
from typing import List, Generator
from paper_model import Paper

class ArxivCrawler:
    def __init__(self, delay=3.0):
        self.base_url = "http://export.arxiv.org/api/query"
        self.delay = delay
        self.last_request_time = 0
        print(f"DEBUG: ArxivCrawler initialized with {delay}s delay")
    
    def _wait_for_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            print(f"DEBUG: Rate limiting - sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
    
    def _make_request(self, query: str, start: int = 0, max_results: int = 100) -> str:
        self._wait_for_rate_limit()
        
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        print(f"DEBUG: Requesting arXiv API - query: {query}, start: {start}, max: {max_results}")
        response = requests.get(self.base_url, params=params)
        self.last_request_time = time.time()
        
        print(f"DEBUG: API response status: {response.status_code}, content length: {len(response.text)}")
        return response.text
    
    def _parse_entry(self, entry) -> Paper:
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
        title = entry.find('atom:title', ns).text.strip()
        abstract = entry.find('atom:summary', ns).text.strip()
        
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns).text
            authors.append(name)
        
        categories = []
        for category in entry.findall('atom:category', ns):
            categories.append(category.get('term'))
        
        pdf_link = None
        for link in entry.findall('atom:link', ns):
            if link.get('type') == 'application/pdf':
                pdf_link = link.get('href')
                break
        
        published = datetime.fromisoformat(entry.find('atom:published', ns).text.replace('Z', '+00:00'))
        updated = datetime.fromisoformat(entry.find('atom:updated', ns).text.replace('Z', '+00:00'))
        
        return Paper(
            arxiv_id=arxiv_id,
            title=title,
            abstract=abstract,
            authors=authors,
            categories=categories,
            pdf_url=pdf_link,
            published_date=published,
            updated_date=updated
        )
    
    def crawl_papers(self, categories: List[str], start_date: datetime, end_date: datetime, batch_size: int = 200) -> Generator[Paper, None, None]:
        category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
        
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        date_query = f'submittedDate:[{start_date_str}0000 TO {end_date_str}2359]'
        full_query = f'({category_query}) AND {date_query}'
        
        print(f"DEBUG: Full query: {full_query}")
        
        start_index = 0
        total_found = 0
        
        while True:
            xml_response = self._make_request(full_query, start_index, batch_size)
            root = ET.fromstring(xml_response)
            
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
            
            total_results = int(root.find('opensearch:totalResults', ns).text)
            start_result = int(root.find('opensearch:startIndex', ns).text)
            items_per_page = int(root.find('opensearch:itemsPerPage', ns).text)
            
            print(f"DEBUG: Batch {start_index//batch_size + 1} - Total: {total_results}, Items: {items_per_page}")
            
            entries = root.findall('atom:entry', ns)
            if not entries:
                print("DEBUG: No more entries found")
                break
            
            batch_papers = []
            for entry in entries:
                paper = self._parse_entry(entry)
                batch_papers.append(paper)
                total_found += 1
            
            # Yield papers in batch
            for paper in batch_papers:
                yield paper
            
            start_index += batch_size
            if start_index >= total_results or start_index >= 1000:  # Limit to 1000 for performance
                print(f"DEBUG: Stopping at {start_index} (limit reached)")
                break
        
        print(f"DEBUG: Crawling completed. Total papers found: {total_found}")
