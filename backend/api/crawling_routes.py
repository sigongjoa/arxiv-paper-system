from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import logging

try:
    # from api.crawling.arxiv_crawler import ArxivCrawler # Removed
    # from api.crawling.rss_crawler import ArxivRSSCrawler # Removed
    from api.crawling.multi_platform_crawler import fetch_arxiv_papers, fetch_biorxiv_papers, fetch_pmc_papers, fetch_plos_papers, fetch_doaj_papers, save_papers_to_db # New import
    from core.paper_database import PaperDatabase as DatabaseManager
    from utils.categories import COMPUTER_CATEGORIES, MATH_CATEGORIES, PHYSICS_CATEGORIES, ALL_CATEGORIES
    from utils import DateCalculator
except ImportError as e:
    logging.error(f"ERROR: Crawling route imports failed - {e}")
    raise

router = APIRouter()

# Initialize components directly
# crawler = ArxivCrawler() # Removed
# rss_crawler = ArxivRSSCrawler() # Removed
db = DatabaseManager()
# create_tables() # main.py의 startup_event에서 호출되므로 제거

logging.basicConfig(level=logging.ERROR)
print("DEBUG: Crawling routes initialized with database component") # Updated message

logger = logging.getLogger(__name__)

def get_papers_by_domain_and_date(domain: str, days_back: int, limit: int, category: str = None):
    """Get papers by domain and date range"""
    papers = []
    logger.debug(f"get_papers_by_domain_and_date called with domain={domain}, days_back={days_back}, limit={limit}, category={category}")

    if days_back == 0:
        # days_back이 0이면 날짜 필터링 없이 모든 논문 가져오기 (최신순)
        papers = db.get_all_papers(limit * 5)
        logger.debug(f"Retrieved {len(papers)} papers from DB for domain {domain} (all papers, limit={limit})")
    else:
        start_date, end_date = DateCalculator.calculate_range(days_back)
        # DB에서 날짜 범위에 맞는 논문 가져오기
        papers = db.get_papers_by_date_range(start_date, end_date, limit * 5)
        logger.debug(f"Retrieved {len(papers)} papers from DB for domain {domain}, date range {start_date.date()} to {end_date.date()}")

    logger.debug(f"Raw papers from DB before domain/category filter: {len(papers)}")
    if papers:
        logger.debug(f"Sample paper dates: {[p.updated_date.isoformat() for p in papers[:3]]}") # published_date 대신 updated_date 사용
    
    # 플랫폼 또는 도메인 필터링
    if domain.lower() in ['arxiv', 'biorxiv', 'pmc', 'plos', 'doaj']:
        papers = [p for p in papers if p.platform.lower() == domain.lower()]
        logger.debug(f"Filtered by platform '{domain}'. Papers remaining: {len(papers)}")
    elif category:
        papers = [p for p in papers if category in str(p.categories)]
        logger.debug(f"Filtered by category '{category}'. Papers remaining: {len(papers)}")
    elif domain.lower() != 'all':
        if domain.lower() == 'computer' or domain.lower() == 'cs':
            filter_cats = COMPUTER_CATEGORIES
        elif domain.lower() == 'math':
            filter_cats = MATH_CATEGORIES
        elif domain.lower() == 'physics':
            filter_cats = PHYSICS_CATEGORIES
        else:
            filter_cats = []
        
        papers = [p for p in papers if any(cat in p.categories for cat in filter_cats)]
        logger.debug(f"Filtered by domain '{domain}' (categories). Papers remaining: {len(papers)}")
    
    return papers[:limit]

# crawl_papers_by_rss 함수는 더 이상 사용되지 않으므로 삭제
# def crawl_papers_by_rss(domain: str, category: str = None, limit: int = 50):
#    # ... existing code ...

def crawl_papers_by_domain(domain: str, days_back: int, category: str = None, limit: int = 50):
    # 이 함수는 arXiv 크롤링 전용이었으므로 통합 크롤링 로직으로 대체
    raise NotImplementedError("crawl_papers_by_domain은 더 이상 사용되지 않습니다. /crawl 엔드포인트를 사용하세요.")


@router.get("/papers")
async def get_papers(
    domain: str = 'all',
    days_back: int = 7,
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

# /crawl-rss 엔드포인트는 더 이상 사용되지 않으므로 삭제
# @router.post("/crawl-rss")
# async def crawl_papers_rss(request: dict):
#    # ... existing code ...

@router.post("/crawl")
async def crawl_papers(request: dict):
    """다중 플랫폼에서 논문 크롤링 및 데이터베이스에 저장"""
    platforms_to_crawl = request.get('platforms', []) # 선택된 플랫폼 목록
    categories = request.get('categories', []) # 선택된 카테고리 목록
    limit_per_platform = request.get('limit_per_platform', 20) # 각 플랫폼에서 가져올 논문 수

    if not platforms_to_crawl:
        raise HTTPException(status_code=400, detail="크롤링할 플랫폼이 지정되지 않았습니다.")
    
    # arXiv 쿼리 생성 (카테고리 기반)
    arxiv_query = 'LLM' # 기본값
    if categories and categories != ['all']:
        arxiv_query = ' OR '.join([f'cat:{cat}' for cat in categories])
    elif categories == ['all']:
        arxiv_query = 'all' # 모든 카테고리 검색

    # 공통 쿼리 생성 (카테고리 기반)
    common_query = 'paper' # 기본값
    if categories and categories != ['all']:
        common_query = ' OR '.join(categories)
    elif categories == ['all']:
        common_query = 'all' # 모든 카테고리 검색 (모든 플랫폼에 적용되는 일반적인 용어)

    try:
        all_crawled_papers_data = []

        for platform in platforms_to_crawl:
            platform = platform.lower() # 소문자로 변환하여 일관성 유지
            print(f"DEBUG_UPDATED_CRAWLER: {platform.upper()} 크롤링 요청 받음 - platforms={platforms_to_crawl}, categories={categories}, limit={limit_per_platform}")

            crawled_papers = [] # 각 플랫폼에서 가져온 논문들을 임시 저장할 리스트

            if platform == 'arxiv':
                crawled_papers = fetch_arxiv_papers(query=arxiv_query, max_results=limit_per_platform)
            elif platform == 'biorxiv':
                crawled_papers = fetch_biorxiv_papers(query=common_query, max_results=limit_per_platform)
            elif platform == 'pmc':
                crawled_papers = fetch_pmc_papers(query=common_query, max_results=limit_per_platform)
            elif platform == 'plos':
                crawled_papers = fetch_plos_papers(query=common_query, max_results=limit_per_platform)
            elif platform == 'doaj':
                crawled_papers = fetch_doaj_papers(query=common_query, max_results=limit_per_platform)
            else:
                print(f"WARNING: 지원하지 않는 플랫폼 요청: {platform}. 스킵합니다.")
                continue # 지원하지 않는 플랫폼은 스킵

            # 가져온 논문 제목 즉시 로깅 (DB 저장 전)
            if crawled_papers:
                print(f"DEBUG_CRAWLER_FETCHED: {platform.upper()}에서 {len(crawled_papers)}개 논문 가져옴. 제목 예시:")
                for i, paper in enumerate(crawled_papers[:5]): # 최대 5개 논문 제목 출력
                    print(f"  - {paper.get('title', '제목 없음')}")
            else:
                print(f"DEBUG_CRAWLER_FETCHED: {platform.upper()}에서 가져온 논문 없음.")

            all_crawled_papers_data.extend(crawled_papers)

        # 모든 플랫폼에서 가져온 논문들을 published_date를 기준으로 최신순으로 정렬
        # published_date가 없는 논문은 리스트의 마지막으로 보냅니다.
        all_crawled_papers_data.sort(key=lambda x: x.get('published_date') or datetime.min, reverse=True)

        # 데이터베이스에 저장
        saved_count = len(all_crawled_papers_data)
        if saved_count > 0:
            save_papers_to_db(all_crawled_papers_data)

        return {"status": "success", "message": f"Crawling completed: {saved_count} new papers processed and saved.", "count": saved_count}
    except Exception as e:
        logging.error(f"Error during multi-platform crawling: {e}", exc_info=True)
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

@router.get("/crawling-status")
async def get_crawling_status():
    """크롤링 시스템의 현재 상태 반환"""
    # 여기에 실제 크롤링 상태 로직을 추가할 수 있습니다.
    # 예: 현재 진행 중인 크롤링 작업 수, 마지막 크롤링 시간 등
    return {"status": "idle", "message": "크롤링 시스템이 유휴 상태입니다.", "last_crawl_time": datetime.now().isoformat()} 