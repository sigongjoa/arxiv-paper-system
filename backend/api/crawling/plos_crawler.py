"""
PLOS (Public Library of Science) 크롤러
공공 과학 도서관 - 오픈 액세스 논문
"""
import requests
import json
from datetime import datetime, timedelta
import logging
import time

class PLOSCrawler:
    def __init__(self):
        self.base_url = "https://api.plos.org/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logging.info("PLOS crawler initialized")

    def crawl_papers(self, categories=None, start_date=None, end_date=None, limit=20):
        """PLOS 논문 크롤링"""
        try:
            logging.info(f"PLOS: Starting crawl - categories={categories}, limit={limit}")
            papers = []
            
            # 검색 쿼리 구성
            query_parts = []
            
            if categories:
                # 카테고리를 PLOS 검색 용어로 변환
                category_terms = []
                for cat in categories:
                    if 'biology' in cat.lower():
                        category_terms.append('subject:"Biology and life sciences"')
                    elif 'medicine' in cat.lower():
                        category_terms.append('subject:"Medicine and health sciences"')
                    elif 'computer' in cat.lower() or 'computational' in cat.lower():
                        category_terms.append('subject:"Computer and information sciences"')
                    else:
                        category_terms.append(f'everything:{cat}')
                
                if category_terms:
                    query_parts.append(f"({' OR '.join(category_terms)})")
            
            # 날짜 필터
            if start_date and end_date:
                date_filter = f'publication_date:[{start_date}T00:00:00Z TO {end_date}T23:59:59Z]'
                query_parts.append(date_filter)
            
            # 기본 쿼리
            if not query_parts:
                query_parts.append('*:*')
            
            query = ' AND '.join(query_parts)
            
            logging.info(f"PLOS: Search query: {query}")
            
            # API 요청
            params = {
                'q': query,
                'fl': 'id,title_display,abstract,author_display,publication_date,journal,subject,article_type',
                'wt': 'json',
                'rows': limit,
                'sort': 'publication_date desc',
                'fq': 'article_type:"Research Article" OR article_type:"Review"'
            }
            
            logging.info(f"PLOS: API URL: {self.base_url}")
            response = self.session.get(self.base_url, params=params, timeout=60)  # 60초로 증가
            response.raise_for_status()
            
            data = response.json()
            logging.debug(f"PLOS: API response - status={response.status_code}, keys={list(data.keys())}")
            
            if 'response' in data and 'docs' in data['response']:
                docs = data['response']['docs']
                logging.info(f"PLOS: Found {len(docs)} papers")
                for doc in docs:
                    paper = self._parse_paper(doc)
                    if paper:
                        papers.append(paper)
                        logging.debug(f"PLOS: Yielding paper: {paper.title[:50]}...")
                        yield paper
                        
                    if len(papers) >= limit:
                        break
            else:
                logging.warning(f"PLOS: No 'response' or 'docs' in API response")
                        
        except Exception as e:
            logging.error(f"PLOS crawl error: {e}")
            import traceback
            traceback.print_exc()

    def _parse_paper(self, doc):
        """논문 데이터 파싱"""
        try:
            from core.models import Paper
            
            # Paper 객체 생성 시 플랫폼 명시
            paper_id = f"PLOS_{doc.get('id', '').replace('/', '_')}"
            title = doc.get('title_display', [''])[0] if isinstance(doc.get('title_display'), list) else doc.get('title_display', '')
            
            # 초록
            abstract_list = doc.get('abstract', [])
            abstract = abstract_list[0] if abstract_list and isinstance(abstract_list, list) else str(abstract_list) if abstract_list else ''
            
            # 저자
            authors = doc.get('author_display', [])
            authors_str = ', '.join(authors) if isinstance(authors, list) else str(authors) if authors else ''
            
            # 카테고리 (subject)
            subjects = doc.get('subject', [])
            if isinstance(subjects, list):
                categories_str = ', '.join(subjects[:3])  # 처음 3개만
            else:
                categories_str = str(subjects) if subjects else 'Science'
            
            # PDF URL
            doi = doc.get('id', '')
            pdf_url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable" if doi else ''
            
            # 발행일
            pub_date = doc.get('publication_date')
            published_date = datetime.now()
            if pub_date:
                try:
                    if isinstance(pub_date, list):
                        pub_date = pub_date[0]
                    # ISO 형식에서 날짜 파싱
                    published_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except:
                    published_date = datetime.now()
            
            # Paper 객체 생성 (플랫폼 명시)
            paper = Paper(
                paper_id=paper_id,
                platform='plos',
                title=title,
                abstract=abstract,
                authors=authors_str.split(', ') if authors_str else [],
                categories=categories_str.split(', ') if categories_str else ['Science'],
                pdf_url=pdf_url,
                published_date=published_date
            )
            
            # 하위 호환성
            paper.arxiv_id = paper_id
            paper.authors = authors_str
            paper.categories = categories_str
            
            return paper
            
        except Exception as e:
            logging.error(f"PLOS parse error: {e}")
            return None
