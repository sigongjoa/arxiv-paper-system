from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import logging

try:
    from api.crawling.arxiv_crawler import ArxivCrawler
    from api.crawling.rss_crawler import ArxivRSSCrawler
    from core.paper_database import PaperDatabase as DatabaseManager # PaperDatabase로 변경
    from utils.categories import COMPUTER_CATEGORIES, MATH_CATEGORIES, PHYSICS_CATEGORIES, ALL_CATEGORIES
    from utils import DateCalculator
except ImportError as e:
    logging.error(f"ERROR: Crawling route imports failed - {e}")
    raise

router = APIRouter()

# Initialize components directly
crawler = ArxivCrawler()
rss_crawler = ArxivRSSCrawler()
db = DatabaseManager()

logging.basicConfig(level=logging.ERROR)
print("DEBUG: Crawling routes initialized with crawler, RSS crawler, database components")

def get_papers_by_domain_and_date(domain: str, days_back: int, limit: int, category: str = None):
    """Get papers by domain and date range"""
    # 날짜 범위 계산
    start_date, end_date = DateCalculator.calculate_range(days_back)
    
    # DB에서 날짜 범위에 맞는 논문 가져오기
    papers = db.get_papers_by_date_range(start_date, end_date, limit * 5)
    
    print(f"DEBUG: Raw papers from DB: {len(papers)}")
    if papers:
        print(f"DEBUG: Sample paper dates: {[p.updated_date.isoformat() for p in papers[:3]]}") # published_date 대신 updated_date 사용
    
    # Domain 필터링
    if category:
        papers = [p for p in papers if category in str(p.categories)]
    elif domain.lower() != 'all':
        if domain.lower() == 'computer' or domain.lower() == 'cs':
            filter_cats = COMPUTER_CATEGORIES
        elif domain.lower() == 'math':
            filter_cats = MATH_CATEGORIES
        elif domain.lower() == 'physics':
            filter_cats = PHYSICS_CATEGORIES
        else:
            filter_cats = []
        
        papers = [p for p in papers if any(cat in p.categories for cat in filter_cats)] # str(p.categories) 대신 직접 p.categories 사용
    
    print(f"DEBUG: Retrieved {len(papers)} papers from DB for domain {domain}, date range {start_date.date()} to {end_date.date()}")
    return papers[:limit]

def crawl_papers_by_rss(domain: str, category: str = None, limit: int = 50):
    """RSS로 논문 크롤링"""
    logging.error(f"RSS crawl started: domain={domain}, category={category}, limit={limit}")
    
    if category:
        categories = [category]
    else:
        if domain.lower() == 'computer' or domain.lower() == 'cs':
            categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.CR']
        elif domain.lower() == 'math':
            categories = ['math.CO', 'math.IT', 'math.ST']
        elif domain.lower() == 'physics':
            categories = ['physics.data-an', 'astro-ph']
        else:
            categories = ['cs.AI']
    
    logging.error(f"RSS crawling categories: {categories}")
    
    saved_count = 0
    for paper_data in rss_crawler.crawl_papers_by_rss(categories, limit):
        # RSS 크롤러는 딕셔너리를 반환하므로 Paper 객체로 변환 필요
        from core.models import Paper # Paper 모델 임포트
        from datetime import datetime

        paper = Paper(
            paper_id=paper_data['arxiv_id'],
            title=paper_data['title'],
            abstract=paper_data['abstract'],
            authors=[a.strip() for a in paper_data['authors'].split(',')] if isinstance(paper_data['authors'], str) else paper_data['authors'],
            categories=[c.strip() for c in paper_data['categories'].split(',')] if isinstance(paper_data['categories'], str) else paper_data['categories'],
            pdf_url=paper_data['pdf_url'],
            published_date=datetime.fromisoformat(paper_data['published_date'].replace('Z', '+00:00') if 'Z' in paper_data['published_date'] else paper_data['published_date']),
            updated_date=datetime.now()
        )

        if db.save_paper(paper):
            saved_count += 1
            logging.error(f"RSS saved paper: {paper.paper_id}")
    
    logging.error(f"RSS crawl completed: {saved_count} papers saved")
    return saved_count

def crawl_papers_by_domain(domain: str, days_back: int, category: str = None, limit: int = 50):
    """Crawl papers by domain or specific category"""
    print(f"DEBUG: crawl_papers_by_domain called with domain={domain}, days_back={days_back}, category={category}, limit={limit}")
    
    start_date, end_date = DateCalculator.calculate_range(days_back)
    
    # If specific category is provided, use only that category
    if category:
        # AI 관련 카테고리는 확장해서 검색
        if category == 'cs.AI':
            categories = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV']  # AI 관련 주요 카테고리
            print(f"DEBUG: Expanding cs.AI to include related categories: {categories}")
        else:
            categories = [category]
        print(f"DEBUG: Crawling specific category {category} from {start_date.date()} to {end_date.date()}, limit: {limit}")
    else:
        # Use all categories for the domain
        if domain.lower() == 'computer' or domain.lower() == 'cs':
            categories = COMPUTER_CATEGORIES
        elif domain.lower() == 'math':
            categories = MATH_CATEGORIES
        elif domain.lower() == 'physics':
            categories = PHYSICS_CATEGORIES
        elif domain.lower() == 'all':
            categories = ALL_CATEGORIES
        else:
            raise ValueError(f"Unknown domain: {domain}")
        
        print(f"DEBUG: Crawling {domain} domain from {start_date.date()} to {end_date.date()}, limit: {limit}")
        print(f"DEBUG: Using categories: {categories[:5]}...") # Show first 5 categories
    
    saved_count = 0
    consecutive_existing = 0
    max_consecutive_existing = 10  # Reduce from 50
    total_processed = 0
    
    for paper in crawler.crawl_papers(categories, start_date, end_date, limit=limit):
        total_processed += 1
        
        # Stop if we have enough new papers
        if saved_count >= limit:
            print(f"DEBUG: Target limit reached - saved {saved_count} papers")
            break
        
        if db.save_paper(paper):
            saved_count += 1
            consecutive_existing = 0  # Reset counter
            print(f"DEBUG: Progress - Processed: {total_processed}, New: {saved_count}")
        else:
            consecutive_existing += 1
        
        # Early termination if too many consecutive existing papers
        if consecutive_existing >= max_consecutive_existing:
            print(f"DEBUG: Early termination - {consecutive_existing} consecutive existing papers")
            break
        
        # Progress update every 20 papers
        if total_processed % 20 == 0:
            print(f"DEBUG: Progress update - Processed: {total_processed}, New: {saved_count}, Skip: {consecutive_existing}")
    
    print(f"DEBUG: Crawling completed - Total processed: {total_processed}, New papers: {saved_count}")
    return saved_count


@router.get("/papers")
async def get_papers(
    domain: str = 'all',
    days_back: int = 3,
    limit: int = 50,
    category: Optional[str] = None
):
    """논문 목록 조회"""
    try:
        papers = get_papers_by_domain_and_date(domain, days_back, limit, category)
        return [p.__dict__ for p in papers] # SQLAlchemy Paper 객체를 딕셔너리로 변환
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting papers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/crawl-rss")
async def crawl_papers_rss(request: dict):
    """RSS 피드를 통해 논문 크롤링"""
    domain = request.get('domain', 'all')
    category = request.get('category', None)
    limit = request.get('limit', 50)
    
    try:
        saved_count = crawl_papers_by_rss(domain, category, limit)
        return {"status": "success", "message": f"RSS Crawl completed: {saved_count} new papers added.", "count": saved_count}
    except Exception as e:
        logging.error(f"Error crawling papers via RSS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RSS Crawl failed: {e}")

@router.post("/crawl")
async def crawl_papers(request: dict):
    """arXiv API를 통해 논문 크롤링 및 데이터베이스에 저장"""
    domain = request.get('domain', 'all')
    days_back = request.get('days_back', 3)
    category = request.get('category', None)
    limit = request.get('limit', 50)
    
    try:
        saved_count = crawl_papers_by_domain(domain, days_back, category, limit)
        return {"status": "success", "message": f"Crawling completed: {saved_count} new papers added.", "count": saved_count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error crawling papers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Crawling failed: {e}")

@router.get("/stats")
async def get_stats():
    """데이터베이스 통계 제공 (총 논문 수)"""
    try:
        total_papers = db.get_total_count()
        return {"total_papers_in_db": total_papers}
    except Exception as e:
        logging.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/categories")
async def get_categories():
    """사용 가능한 카테고리 목록 제공"""
    return {
        "computer_science": list(COMPUTER_CATEGORIES),
        "mathematics": list(MATH_CATEGORIES),
        "physics": list(PHYSICS_CATEGORIES),
        "all_categories": list(ALL_CATEGORIES)
    }

@router.get("/health")
async def health_check():
    """API 헬스 체크"""
    return {"status": "ok", "message": "Crawling API is healthy"} 