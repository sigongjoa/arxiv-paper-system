"""
DOAJ (Directory of Open Access Journals) 크롤러
오픈 액세스 저널 디렉토리
"""
import requests
import json
from datetime import datetime, timedelta
import logging
import time

class DOAJCrawler:
    def __init__(self):
        self.base_url = "https://doaj.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logging.info("DOAJ crawler initialized")

    def crawl_papers(self, categories=None, start_date=None, end_date=None, limit=20):
        """DOAJ 논문 크롤링"""
        try:
            logging.info(f"DOAJ: Starting crawl - categories={categories}, limit={limit}")
            papers = []
            
            # 검색 쿼리 구성
            query_parts = []
            
            if categories:
                # 카테고리를 DOAJ 검색 용어로 변환
                category_terms = []
                for cat in categories:
                    if 'computer' in cat.lower() or 'engineering' in cat.lower():
                        category_terms.append('bibjson.subject.term:"Computer Science"')
                    elif 'medicine' in cat.lower():
                        category_terms.append('bibjson.subject.term:"Medicine"')
                    elif 'biology' in cat.lower():
                        category_terms.append('bibjson.subject.term:"Biology"')
                    elif 'education' in cat.lower():
                        category_terms.append('bibjson.subject.term:"Education"')
                    elif 'psychology' in cat.lower():
                        category_terms.append('bibjson.subject.term:"Psychology"')
                    else:
                        category_terms.append(f'bibjson.title:"{cat}" OR bibjson.abstract:"{cat}"')
                
                if category_terms:
                    query_parts.append(f"({' OR '.join(category_terms)})")
            
            # 날짜 필터
            if start_date and end_date:
                date_filter = f'bibjson.year:[{start_date[:4]} TO {end_date[:4]}]'
                query_parts.append(date_filter)
            
            # 기본 쿼리 (와일드카드 금지, 간단한 텍스트 검색)
            if query_parts:
                query = ' AND '.join(query_parts)
            else:
                # * 대신 일반적인 검색어 사용 (와일드카드 금지)
                query = 'science OR research OR article'
            
            logging.info(f"DOAJ: Search query: {query}")
            
            # API 요청 (v1 사용, 쿼리를 URL 경로에 포함)
            from urllib.parse import quote
            encoded_query = quote(query)
            url = f"{self.base_url}/v1/search/articles/{encoded_query}"
            params = {
                'pageSize': limit,
                'sort': 'created_date:desc'
            }
            
            logging.info(f"DOAJ: API URL: {url}")
            response = self.session.get(url, params=params, timeout=60)  # 60초로 증가
            response.raise_for_status()
            
            data = response.json()
            logging.debug(f"DOAJ: API response - status={response.status_code}, keys={list(data.keys())}")
            
            if 'results' in data:
                results = data['results']
                logging.info(f"DOAJ: Found {len(results)} papers")
                for item in results:
                    paper = self._parse_paper(item)
                    if paper:
                        papers.append(paper)
                        logging.debug(f"DOAJ: Yielding paper: {paper.title[:50]}...")
                        yield paper
                        
                    if len(papers) >= limit:
                        break
            else:
                logging.warning(f"DOAJ: No 'results' in API response")
                        
        except Exception as e:
            logging.error(f"DOAJ crawl error: {e}")
            import traceback
            traceback.print_exc()

    def _parse_paper(self, item):
        """논문 데이터 파싱"""
        try:
            from core.models import Paper
            
            bibjson = item.get('bibjson', {})
            
            # 논문 정보 추출
            paper_id = f"DOAJ_{item.get('id', '').replace('/', '_')}"
            title = bibjson.get('title', '')
            abstract = bibjson.get('abstract', '')
            
            # 저자
            authors = []
            for author in bibjson.get('author', []):
                name = author.get('name', '')
                if name:
                    authors.append(name)
            authors_str = ', '.join(authors)
            
            # 카테고리 (subject)
            subjects = []
            for subj in bibjson.get('subject', []):
                term = subj.get('term', '')
                if term:
                    subjects.append(term)
            categories_str = ', '.join(subjects[:3]) if subjects else 'General'
            
            # PDF URL
            links = bibjson.get('link', [])
            pdf_url = ''
            for link in links:
                if link.get('type') == 'fulltext' and 'pdf' in link.get('content_type', '').lower():
                    pdf_url = link.get('url', '')
                    break
            
            if not pdf_url:
                # 일반 링크 사용
                for link in links:
                    if link.get('type') == 'fulltext':
                        pdf_url = link.get('url', '')
                        break
            
            # 발행일
            year = bibjson.get('year')
            month = bibjson.get('month')
            
            published_date = datetime.now()
            if year:
                try:
                    published_date = datetime(
                        int(year),
                        int(month) if month else 1,
                        1
                    )
                except:
                    published_date = datetime.now()
            
            # Paper 객체 생성 (플랫폼 명시)
            paper = Paper(
                paper_id=paper_id,
                platform='doaj',
                title=title,
                abstract=abstract,
                authors=authors,
                categories=subjects[:3] if subjects else ['General'],
                pdf_url=pdf_url,
                published_date=published_date
            )
            
            # 하위 호환성
            paper.arxiv_id = paper_id
            paper.authors = authors_str
            paper.categories = categories_str
            
            return paper
            
        except Exception as e:
            logging.error(f"DOAJ parse error: {e}")
            return None
