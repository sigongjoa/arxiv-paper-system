import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta, timezone
from typing import List, Generator
import sys
import os

# Add path for models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.models import Paper
from core.embedding_manager import EmbeddingManager

class ArxivCrawler:
    def __init__(self, delay=3.0):
        self.base_url = "http://export.arxiv.org/api/query"
        self.delay = delay
        self.last_request_time = 0
        self.embedding_manager = EmbeddingManager()
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
            'sortBy': 'submittedDate',  # 최신 제출 논문이 먼저 오게 하기
            'sortOrder': 'descending'
        }
        
        # 1. URL 로그 출력
        full_url = f"{self.base_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
        print(f"DEBUG_URL: {full_url}")
        print(f"DEBUG: Requesting arXiv API - query: {query}, start={start}, max={max_results}")
        
        response = requests.get(self.base_url, params=params)
        self.last_request_time = time.time()
        
        print(f"DEBUG: API response status: {response.status_code}, length={len(response.text)}")
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
        
        # DEBUG: 날짜 정보 출력 + 더 자세한 정보
        # arXiv API 원본 데이터 확인용
        raw_published = entry.find('atom:published', ns).text
        raw_updated = entry.find('atom:updated', ns).text
        print(f"DEBUG_XML: {arxiv_id} - 원본 published='{raw_published}', updated='{raw_updated}'")
        
        # Generate embedding
        text_to_embed = f"{title}. {abstract}"
        embedding = self.embedding_manager.get_embedding(text_to_embed)

        return Paper(
            paper_id=arxiv_id,
            platform='arxiv',
            title=title,
            abstract=abstract,
            authors=authors,
            categories=categories,
            pdf_url=pdf_link,
            published_date=published,
            updated_date=updated,
            embedding=embedding.tolist() if embedding is not None else None
        )
    
    def crawl_papers(self, categories: List[str], start_date: datetime, end_date: datetime, batch_size: int = None, limit: int = 50) -> Generator[Paper, None, None]:
        if categories == ['all'] or len(categories) > 50:
            # 전체 검색 또는 카테고리가 너무 많을 때
            full_query = 'all'
        else:
            category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
            full_query = f'({category_query})'
        
        # arXiv API 날짜 필터 지원 안함 - 단순 카테고리 검색 + 최신순 정렬만 사용
        
        # 2. 쿼리 문자열 검증
        print(f"DEBUG_QUERY: Original query='{full_query}'")
        if 'submittedDate:' in full_query:
            print("WARNING: 날짜 필터가 쿼리에 포함되어 있음!")
        if 'cat:' in full_query and len(full_query) < 50:
            print("WARNING: 매우 좋은 카테고리 필터 감지")
        
        print(f"DEBUG: Full query (WORKING): {full_query}")
        print(f"DEBUG: Getting latest {limit} papers (no date filtering)")
        
        # batch_size를 limit에 맞춰 조정
        if batch_size is None:
            batch_size = min(limit * 2, 50)  # limit의 2배 또는 최대 50
        
        start_index = 0
        total_found = 0
        papers_yielded = 0
        
        while papers_yielded < limit:
            # API 요청 크기를 limit에 맞춰 제한
            api_batch_size = min(batch_size, limit * 2)
            xml_response = self._make_request(full_query, start_index, api_batch_size)
            
            # Debug: print first 500 chars of response
            print(f"DEBUG: XML Response preview: {xml_response[:500]}...")
            
            root = ET.fromstring(xml_response)
            
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
            
            total_results = int(root.find('opensearch:totalResults', ns).text)
            start_result = int(root.find('opensearch:startIndex', ns).text)
            items_per_page = int(root.find('opensearch:itemsPerPage', ns).text)
            
            # 3. 페이징 로직 체크
            print(f"DEBUG_PAGING: Batch {start_index//batch_size + 1} - start_index={start_index}, batch_size={batch_size}")
            print(f"DEBUG: Batch {start_index//batch_size + 1} - Total: {total_results}, Items: {items_per_page}")
            
            entries = root.findall('atom:entry', ns)
            if not entries:
                print("DEBUG: No more entries found")
                break
            
            for entry in entries:
                if papers_yielded >= limit:
                    print(f"DEBUG: Reached limit ({limit}) papers")
                    break
                    
                paper = self._parse_entry(entry)
                total_found += 1
                papers_yielded += 1
                
                # 4. 최신 논문 ID 체크 (2506.xxxxx 형태인지)
                arxiv_year_month = paper.arxiv_id[:4] if len(paper.arxiv_id) >= 4 else 'unknown'
                if arxiv_year_month.startswith('250'):
                    print(f"DEBUG_LATEST: Found 2025 paper: {paper.arxiv_id}")
                
                print(f"DEBUG: Paper {papers_yielded}/{limit}: {paper.arxiv_id} - 발행일:{paper.published_date.date()}, 출판일:{paper.updated_date.date()}, 제목:{paper.title[:30]}...")
                
                yield paper
            
            # 중단 조건 체크
            if papers_yielded >= limit:
                print(f"DEBUG: Found {papers_yielded} papers - Stop crawling")
                break
            
            start_index += batch_size
            if start_index >= total_results:
                print(f"DEBUG: Stopping at start_index={start_index} (no more results)")
                break
        
        print(f"DEBUG: Crawling completed. Total processed: {total_found}, Yielded: {papers_yielded}")
