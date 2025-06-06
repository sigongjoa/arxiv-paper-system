"""
BioRxiv/MedRxiv 크롤러
생명과학 및 의학 연구 프리프린트 서버
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import time

class BioRxivCrawler:
    def __init__(self):
        self.base_url = "https://api.biorxiv.org/details"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logging.info("BioRxiv crawler initialized")

    def crawl_papers(self, categories=None, start_date=None, end_date=None, limit=20):
        """비오아카이브/메드아카이브 논문 크롤링"""
        try:
            logging.info(f"BioRxiv: Starting crawl - categories={categories}, limit={limit}")
            papers = []
            
            # BioRxiv와 MedRxiv 모두 크롤링
            servers = ['biorxiv', 'medrxiv']
            
            for server in servers:
                if len(papers) >= limit:
                    break
                    
                logging.info(f"BioRxiv: Crawling {server}: latest {limit} papers")
                
                # 최신 N개 논문 요청
                url = f"{self.base_url}/{server}/{limit}"
                logging.info(f"BioRxiv: API URL: {url}")
                
                response = self.session.get(url, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                logging.info(f"BioRxiv: API response - status={response.status_code}, data_keys={list(data.keys())}")
                
                if 'collection' in data:
                    logging.info(f"BioRxiv: Found {len(data['collection'])} papers from {server}")
                    for item in data['collection']:
                        if len(papers) >= limit:
                            break
                            
                        paper = self._parse_paper(item, server)
                        if paper:
                            papers.append(paper)
                            logging.info(f"BioRxiv: Yielding paper: {paper.title[:50]}...")
                            yield paper
                else:
                    logging.warning(f"BioRxiv: No 'collection' key in response from {server}")
                            
                time.sleep(1)
                
        except Exception as e:
            logging.error(f"BioRxiv crawl error: {e}")
            import traceback
            traceback.print_exc()

    def _parse_paper(self, item, server):
        """논문 데이터 파싱"""
        try:
            from core.models import Paper
            
            # Paper 객체 생성 시 필수 값들을 바로 넘김
            paper_id = f"{server}_{item.get('doi', '').replace('/', '_')}"
            title = item.get('title', '')
            abstract = item.get('abstract', '')
            authors_str = item.get('authors', '')
            authors = authors_str.split(';') if authors_str else []
            category = item.get('category', server)
            pdf_url = f"https://www.{server}.org/content/10.1101/{item.get('doi', '').split('/')[-1]}v1.full.pdf"
            published_date = datetime.strptime(item.get('date', ''), '%Y-%m-%d') if item.get('date') else datetime.now()
            
            paper = Paper(
                paper_id=paper_id,
                platform=server, 
                title=title,
                abstract=abstract,
                authors=authors,
                categories=[category],
                pdf_url=pdf_url,
                published_date=published_date
            )
            
            # 하위 호환성을 위한 속성들
            paper.arxiv_id = paper_id
            paper.authors = ', '.join(authors) if authors else ''
            paper.categories = category
            
            return paper
            
        except Exception as e:
            logging.error(f"BioRxiv parse error: {e}")
            import traceback
            traceback.print_exc()
            return None
