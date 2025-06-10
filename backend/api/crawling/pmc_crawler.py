"""
PMC (PubMed Central) 크롤러
NIH 공공 의학 논문 데이터베이스
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import time

class PMCCrawler:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logging.info("PMC crawler initialized")

    def crawl_papers(self, categories=None, start_date=None, end_date=None, limit=20):
        """PMC 논문 크롤링"""
        try:
            logging.info(f"PMC: Starting crawl - categories={categories}, limit={limit}")
            papers = []
            
            # 검색 쿼리 구성
            query_terms = []
            
            if categories:
                # 카테고리를 PMC 검색 용어로 변환
                category_terms = []
                for cat in categories:
                    if 'medicine' in cat.lower() or 'medical' in cat.lower():
                        category_terms.append('medicine[MeSH Terms]')
                    elif 'biology' in cat.lower() or 'biomedical' in cat.lower():
                        category_terms.append('biology[MeSH Terms]')
                    elif 'genetics' in cat.lower():
                        category_terms.append('genetics[MeSH Terms]')
                    else:
                        category_terms.append(f'{cat}[Title/Abstract]')
                
                if category_terms:
                    query_terms.append(f"({' OR '.join(category_terms)})")
            
            # 날짜 필터
            if start_date and end_date:
                date_filter = f'("{start_date}"[Publication Date] : "{end_date}"[Publication Date])'
                query_terms.append(date_filter)
            
            # 기본 쿼리
            if not query_terms:
                query_terms.append('medicine[MeSH Terms] OR biology[MeSH Terms]')
            
            query = ' AND '.join(query_terms)
            
            logging.info(f"PMC: Search query: {query}")
            
            # 검색 실행
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                'db': 'pmc',
                'term': query,
                'retmax': limit,
                'retmode': 'xml',
                'sort': 'pub_date',
                'tool': 'arxiv_system',
                'email': 'research@example.com'
            }
            
            logging.info(f"PMC: API URL: {search_url}")
            response = self.session.get(search_url, params=search_params, timeout=60)
            response.raise_for_status()
            
            # XML 응답 파싱
            try:
                root = ET.fromstring(response.content)
                id_list = root.findall('.//Id')
                ids = [id_elem.text for id_elem in id_list]
                logging.info(f"PMC: Found {len(ids)} paper IDs")
                
                # 논문 상세 정보 가져오기
                if ids:
                    for paper_id in ids[:limit]:
                        try:
                            paper = self._fetch_paper_details(paper_id)
                            if paper:
                                papers.append(paper)
                                logging.debug(f"PMC: Yielding paper: {paper.title[:50]}...")
                                yield paper
                        except Exception as e:
                            logging.error(f"PMC: Error processing paper {paper_id}: {e}")
                            continue
                            
                        time.sleep(0.5)  # Rate limiting
                else:
                    logging.warning("PMC: No paper IDs found")
                        
            except ET.ParseError as e:
                logging.error(f"PMC: XML parse error: {e}")
                logging.error(f"PMC: Response content: {response.text[:500]}")
                return
                        
        except Exception as e:
            logging.error(f"PMC crawl error: {e}")
            import traceback
            traceback.print_exc()

    def _fetch_paper_details(self, paper_id):
        """논문 상세 정보 가져오기"""
        try:
            from core.models import Paper
            
            fetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                'db': 'pmc',
                'id': paper_id,
                'rettype': 'xml',
                'tool': 'arxiv_system',
                'email': 'research@example.com'
            }
            
            response = self.session.get(fetch_url, params=fetch_params, timeout=60)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # 논문 정보 추출
            title = ''
            title_elem = root.find('.//article-title')
            if title_elem is not None:
                title = title_elem.text or ''
            
            abstract = ''
            abstract_elem = root.find('.//abstract/p')
            if abstract_elem is None:
                abstract_elem = root.find('.//abstract')
            if abstract_elem is not None:
                abstract = abstract_elem.text or ''
            
            # 저자 추출
            authors = []
            for contrib in root.findall('.//contrib[@contrib-type="author"]'):
                given_names = contrib.find('.//given-names')
                surname = contrib.find('.//surname')
                if given_names is not None and surname is not None:
                    authors.append(f"{given_names.text} {surname.text}")
            
            # 카테고리 추출
            subjects = []
            for subj in root.findall('.//subject'):
                if subj.text:
                    subjects.append(subj.text)
            
            # 발행일 추출
            pub_date = root.find('.//pub-date[@pub-type="epub"]')
            if pub_date is None:
                pub_date = root.find('.//pub-date')
                
            published_date = datetime.now()
            if pub_date is not None:
                year = pub_date.find('year')
                month = pub_date.find('month')
                day = pub_date.find('day')
                
                if year is not None:
                    try:
                        published_date = datetime(
                            int(year.text),
                            int(month.text) if month is not None else 1,
                            int(day.text) if day is not None else 1
                        )
                    except:
                        published_date = datetime.now()
            
            # Paper 객체 생성
            paper = Paper(
                paper_id=f"PMC{paper_id}",
                platform='pmc',
                title=title,
                abstract=abstract,
                authors=authors,
                categories=subjects if subjects else ['Medicine'],
                pdf_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{paper_id}/pdf/",
                published_date=published_date
            )
            
            # 하위 호환성
            paper.arxiv_id = f"PMC{paper_id}"
            paper.authors = ', '.join(authors) if authors else ''
            paper.categories = ', '.join(subjects) if subjects else 'Medicine'
            
            return paper
            
        except Exception as e:
            logging.error(f"PMC fetch error for {paper_id}: {e}")
            return None
