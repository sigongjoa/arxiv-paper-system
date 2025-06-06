"""
CORE (COnnecting REpositories) 크롤러
세계 최대 학술 논문 집합체 (API 키 필요)
"""
import requests
import json
import os
from datetime import datetime, timedelta
import logging
import time

class CORECrawler:
    def __init__(self):
        self.base_url = "https://api.core.ac.uk/v3"
        self.api_key = os.getenv('CORE_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Authorization': f'Bearer {self.api_key}' if self.api_key else None
        })
        logging.error(f"CORE crawler initialized - API key: {'✓' if self.api_key else '✗'}")

    def crawl_papers(self, categories=None, start_date=None, end_date=None, limit=20):
        """CORE 논문 크롤링"""
        try:
            logging.error(f"CORE: Starting crawl - categories={categories}, limit={limit}")
            if not self.api_key:
                logging.error("CORE: API key not found - using demo data")
                # API 키가 없을 때 데모 데이터 반환
                yield from self._get_demo_papers(limit)
                return
                
            papers = []
            
            # 검색 쿼리 구성
            query_parts = []
            
            if categories:
                # 카테고리를 CORE 검색 용어로 변환
                category_terms = []
                for cat in categories:
                    if 'computer' in cat.lower():
                        category_terms.append('computer science')
                    elif 'medicine' in cat.lower():
                        category_terms.append('medicine')
                    elif 'engineering' in cat.lower():
                        category_terms.append('engineering')
                    elif 'biology' in cat.lower():
                        category_terms.append('biology')
                    else:
                        category_terms.append(cat.replace('_', ' '))
                
                if category_terms:
                    query_parts.extend(category_terms)
            
            # 기본 쿼리
            if not query_parts:
                query_parts = ['computer science', 'artificial intelligence']
            
            query = ' OR '.join(query_parts)
            
            logging.error(f"CORE: Search query: {query}")
            
            # API 요청
            search_url = f"{self.base_url}/search/works"
            params = {
                'q': query,
                'limit': limit,
                'sort': 'publishedDate:desc',
                'exclude': ['fullText']  # 전체 텍스트 제외로 응답 크기 줄이기
            }
            
            logging.error(f"CORE: API URL: {search_url}")
            response = self.session.get(search_url, params=params, timeout=60)  # 60초로 증가
            response.raise_for_status()
            
            data = response.json()
            logging.error(f"CORE: API response - status={response.status_code}, keys={list(data.keys())}")
            
            if 'results' in data:
                results = data['results']
                logging.error(f"CORE: Found {len(results)} papers")
                for item in results:
                    paper = self._parse_paper(item)
                    if paper:
                        papers.append(paper)
                        logging.error(f"CORE: Yielding paper: {paper.title[:50]}...")
                        yield paper
                        
                    if len(papers) >= limit:
                        break
            else:
                logging.error(f"CORE: No 'results' in API response")
                        
        except Exception as e:
            logging.error(f"CORE crawl error: {e}")
            import traceback
            traceback.print_exc()
            
            # 에러 시 데모 데이터 반환
            logging.error("CORE: Falling back to demo data")
            yield from self._get_demo_papers(limit)

    def _parse_paper(self, item):
        """논문 데이터 파싱"""
        try:
            from core.models import Paper
            
            # 논문 정보 추출
            paper_id = f"CORE_{item.get('id', '')}"
            title = item.get('title', '')
            abstract = item.get('abstract', '')
            
            # 저자
            authors = []
            for author in item.get('authors', []):
                name = author.get('name', '')
                if name:
                    authors.append(name)
            authors_str = ', '.join(authors)
            
            # 카테고리 (subject)
            subjects = item.get('subjects', [])
            categories_str = ', '.join(subjects[:3]) if subjects else 'General'
            
            # PDF URL
            download_url = item.get('downloadUrl', '')
            pdf_url = download_url
            if not pdf_url:
                # 대체 URL
                urls = item.get('urls', [])
                pdf_url = urls[0] if urls else ''
            
            # 발행일
            pub_date = item.get('publishedDate')
            published_date = datetime.now()
            if pub_date:
                try:
                    published_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except:
                    published_date = datetime.now()
            
            # Paper 객체 생성 (플랫폼 명시)
            paper = Paper(
                paper_id=paper_id,
                platform='core',
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
            logging.error(f"CORE parse error: {e}")
            return None

    def _get_demo_papers(self, limit=20):
        """API 키가 없을 때 데모 데이터 반환"""
        try:
            from core.models import Paper
            
            demo_papers = [
                {
                    'title': 'Artificial Intelligence in Healthcare: A Comprehensive Review',
                    'abstract': 'This paper provides a comprehensive review of AI applications in healthcare, covering machine learning, deep learning, and their clinical implementations.',
                    'authors': 'Smith, J., Johnson, M., Williams, K.',
                    'categories': 'Computer Science, Medicine, Artificial Intelligence',
                    'doi': '10.1000/demo001'
                },
                {
                    'title': 'Deep Learning for Natural Language Processing: Recent Advances',
                    'abstract': 'An overview of recent advances in deep learning approaches for natural language processing tasks including sentiment analysis and machine translation.',
                    'authors': 'Chen, L., Rodriguez, A., Kim, S.',
                    'categories': 'Computer Science, Natural Language Processing',
                    'doi': '10.1000/demo002'
                },
                {
                    'title': 'Computer Vision Applications in Autonomous Vehicles',
                    'abstract': 'This study examines the role of computer vision technologies in autonomous vehicle systems and their impact on transportation safety.',
                    'authors': 'Brown, D., Taylor, R., Wilson, P.',
                    'categories': 'Computer Science, Computer Vision, Engineering',
                    'doi': '10.1000/demo003'
                }
            ]
            
            for i, demo in enumerate(demo_papers[:limit]):
                # Paper 객체 생성 (플랫폼 명시)
                paper_id = f"CORE_DEMO_{i+1}"
                paper = Paper(
                    paper_id=paper_id,
                    platform='core',
                    title=demo['title'],
                    abstract=demo['abstract'],
                    authors=demo['authors'].split(', '),
                    categories=demo['categories'].split(', '),
                    pdf_url=f"https://demo.core.ac.uk/papers/{demo['doi']}.pdf",
                    published_date=datetime.now() - timedelta(days=i*2)
                )
                
                # 하위 호환성
                paper.arxiv_id = paper_id
                paper.authors = demo['authors']
                paper.categories = demo['categories']
                
                logging.error(f"Generated CORE demo paper: {paper.title[:50]}...")
                yield paper
                
        except Exception as e:
            logging.error(f"Demo paper generation error: {e}")
