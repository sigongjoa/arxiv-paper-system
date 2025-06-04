import requests
import xml.etree.ElementTree as ET
import logging
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class ProcessorImpl:
    def __init__(self):
        # HTTP 세션 설정 (재시도 로직 포함)
        self.session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 연결 타임아웃 설정
        self.session.headers.update({
            'User-Agent': 'arXiv-to-Shorts/1.0 (https://github.com/example/arxiv-to-shorts)'
        })
        
    def process_arxiv_paper(self, arxiv_id):
        logging.info(f"Starting paper processing for arXiv ID: {arxiv_id}")
        clean_id = arxiv_id.replace('v1', '').replace('v2', '').replace('v3', '')
        
        logging.info(f"Fetching paper data from arXiv API...")
        url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
        
        # 안정적인 요청을 위한 재시도 로직
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logging.info(f"arXiv API request attempt {attempt + 1}/{max_retries}")
                response = self.session.get(url, timeout=(10, 30))  # (connect_timeout, read_timeout)
                
                if response.status_code == 200:
                    break
                else:
                    logging.warning(f"arXiv API returned status {response.status_code}")
                    if attempt == max_retries - 1:
                        raise Exception(f"arXiv API error: {response.status_code}")
                        
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                logging.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"arXiv API network error after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # 지수 백오프
        
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entries = root.findall('atom:entry', ns)
        if not entries:
            logging.error(f"Paper {arxiv_id} not found")
            raise Exception(f"Paper {arxiv_id} not found in arXiv")
        
        entry = entries[0]
        
        paper_id = entry.find('atom:id', ns).text.split('/')[-1]
        title = entry.find('atom:title', ns).text.strip()
        abstract = entry.find('atom:summary', ns).text.strip()
        
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns).text
            authors.append(name)
        
        categories = []
        for category in entry.findall('atom:category', ns):
            categories.append(category.get('term'))
        
        paper_dict = {
            'arxiv_id': paper_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'categories': categories
        }
        
        logging.info(f"Successfully processed paper: {title}")
        logging.info(f"Authors: {', '.join(authors)}")
        logging.info(f"Categories: {', '.join(categories)}")
        
        return {
            'paper': paper_dict,
            'summary': abstract,
            'status': 'completed'
        }
