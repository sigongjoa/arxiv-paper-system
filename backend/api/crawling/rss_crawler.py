import feedparser
import requests
import logging
import re
from datetime import datetime
from typing import List, Generator
import sys
import os

# Add path for models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.models import Paper

class ArxivRSSCrawler:
    def __init__(self):
        self.base_rss_url = "https://export.arxiv.org/rss"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logging.info("ArxivRSSCrawler initialized")
    
    def _parse_rss_entry(self, entry) -> Paper:
        try:
            # arXiv ID 추출
            arxiv_id = entry.link.split('/')[-1]
            
            title = entry.title.strip()
            
            # 초록 추출
            summary = entry.summary if hasattr(entry, 'summary') else ""
            if "Abstract: " in summary:
                abstract = summary.split("Abstract: ", 1)[1].strip()
            else:
                abstract = summary.strip()
            
            # 작성자 추출 (summary에서)
            authors = []
            if "Authors: " in summary:
                try:
                    author_part = summary.split("Authors: ")[1].split("Abstract:")[0].strip()
                    authors = [name.strip() for name in author_part.split(',')]
                except:
                    authors = ['Unknown']
            else:
                authors = ['Unknown']
            
            # 카테고리
            categories = ['cs.AI']
            
            # 날짜
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6])
            else:
                published_date = datetime.now()
            
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            logging.debug(f"RSS parsed: {arxiv_id} - {title[:50]}...")
            
            return Paper(
                paper_id=arxiv_id,
                platform='arxiv',
                title=title,
                abstract=abstract,
                authors=authors,
                categories=categories,
                pdf_url=pdf_url,
                published_date=published_date,
                updated_date=published_date
            )
            
        except Exception as e:
            logging.error(f"RSS parsing error: {str(e)}")
            raise
    
    def crawl_papers(self, categories: List[str], start_date, end_date, limit: int = 50) -> Generator[Paper, None, None]:
        return self.crawl_papers_by_rss(categories, limit)
    
    def crawl_papers_by_rss(self, categories: List[str], limit: int = 50) -> Generator[Paper, None, None]:
        papers_count = 0
        
        for category in categories:
            if papers_count >= limit:
                break
            rss_url = f"{self.base_rss_url}/{category}"
            logging.info(f"Fetching RSS: {rss_url}")
            
            try:
                # requests로 직접 가져오기 (working_rss_test.py 방식)
                response = self.session.get(rss_url, timeout=15)
                response.raise_for_status()
                
                logging.debug(f"HTTP 상태: {response.status_code}, 응답 길이: {len(response.text)}")
                
                # feedparser로 파싱
                feed = feedparser.parse(response.text)
                
                logging.debug(f"Feed title: {feed.feed.get('title', 'No title')}")
                logging.debug(f"Entries found: {len(feed.entries)}")
                
                if not feed.entries:
                    logging.warning(f"No entries for {category}")
                    continue
                
                for i, entry in enumerate(feed.entries):
                    if papers_count >= limit:
                        break
                    
                    try:
                        paper = self._parse_rss_entry(entry)
                        papers_count += 1
                        logging.debug(f"RSS paper {papers_count}/{limit}: {paper.paper_id}")
                        yield paper
                        
                    except Exception as e:
                        logging.error(f"Entry {i} parse error: {str(e)}")
                        continue
                        
            except Exception as e:
                logging.error(f"RSS fetch error for {category}: {str(e)}")
                continue
        
        logging.info(f"RSS crawling completed: {papers_count} papers total")
