from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

router = APIRouter()

# 메모리에 크롤링 결과 저장
crawled_papers = []

@router.get("/papers")
async def get_papers(
    domain: str = 'all',
    days_back: int = 0,
    limit: int = 50,
    category: Optional[str] = None
):
    """메모리에서 크롤링된 논문 반환"""
    logging.error(f"GET /papers: returning {len(crawled_papers)} crawled papers")
    
    # 메모리에서 논문 반환 (필터링 없이)
    papers_to_return = crawled_papers[-limit:] if len(crawled_papers) > limit else crawled_papers
    
    return papers_to_return

@router.get("/stats")
async def get_stats():
    """메모리 통계"""
    return {
        'total_count': len(crawled_papers),
        'last_updated': datetime.now().isoformat()
    }

@router.post("/crawl")
async def crawl_papers(request: dict):
    """크롤링 후 메모리에 저장"""
    global crawled_papers
    
    domain = request.get('domain', 'all')
    limit = request.get('limit', 20)
    
    logging.error(f"Crawling: domain={domain}, limit={limit}")
    
    try:
        # 기존 결과 초기화
        crawled_papers = []
        
        # BioRxiv 크롤러 사용
        from api.crawling.biorxiv_crawler import BioRxivCrawler
        crawler = BioRxivCrawler()
        
        for paper in crawler.crawl_papers(categories=None, limit=limit):
            paper_dict = {
                'arxiv_id': getattr(paper, 'arxiv_id', ''),
                'title': getattr(paper, 'title', ''),
                'abstract': getattr(paper, 'abstract', ''),
                'authors': getattr(paper, 'authors', ''),
                'categories': getattr(paper, 'categories', ''),
                'pdf_url': getattr(paper, 'pdf_url', ''),
                'published_date': getattr(paper, 'published_date', datetime.now()).isoformat(),
                'updated_date': datetime.now().isoformat()
            }
            crawled_papers.append(paper_dict)
            logging.error(f"Added paper: {paper_dict['title'][:50]}...")
        
        logging.error(f"Crawled {len(crawled_papers)} papers")
        
        return {
            'status': 'success',
            'saved_count': len(crawled_papers),
            'domain': domain,
            'limit': limit
        }
        
    except Exception as e:
        logging.error(f"Crawling failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
