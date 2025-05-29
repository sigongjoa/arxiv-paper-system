from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import sys
import os

# Add root directory to path
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_path)

try:
    from arxiv_crawler import ArxivCrawler
    from database import PaperDatabase  
    from categories import COMPUTER_CATEGORIES, MATH_CATEGORIES, PHYSICS_CATEGORIES, ALL_CATEGORIES
    from backend.core.llm_summarizer import LLMSummarizer
except ImportError as e:
    print(f"ERROR: Failed to import modules - {e}")
    raise

router = APIRouter()

# Initialize components directly
crawler = ArxivCrawler()
db = PaperDatabase()
llm_summarizer = LLMSummarizer()
print("DEBUG: Routes initialized with crawler, database and LLM summarizer")

def get_papers_by_domain_and_date(domain: str, days_back: int, limit: int, category: str = None):
    """Get papers by domain and date range"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    papers = db.get_papers_by_date_range(start_date, end_date, limit * 3)  # Get more to filter
    
    # Filter by specific category if provided
    if category:
        papers = [p for p in papers if category in p.categories]
    elif domain.lower() != 'all':
        if domain.lower() == 'computer':
            filter_cats = COMPUTER_CATEGORIES
        elif domain.lower() == 'math':
            filter_cats = MATH_CATEGORIES
        elif domain.lower() == 'physics':
            filter_cats = PHYSICS_CATEGORIES
        else:
            filter_cats = []
        
        papers = [p for p in papers if any(cat in filter_cats for cat in p.categories)]
    
    return papers[:limit]

def crawl_papers_by_domain(domain: str, days_back: int, category: str = None, limit: int = 50):
    """Crawl papers by domain or specific category"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # If specific category is provided, use only that category
    if category:
        categories = [category]
        print(f"DEBUG: Crawling specific category {category} from {start_date.date()} to {end_date.date()}, limit: {limit}")
    else:
        # Use all categories for the domain
        if domain.lower() == 'computer':
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
    
    saved_count = 0
    consecutive_existing = 0
    max_consecutive_existing = 10  # Reduce from 50
    total_processed = 0
    
    for paper in crawler.crawl_papers(categories, start_date, end_date):
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
    days_back: int = 7,
    limit: int = 50,
    category: Optional[str] = None
):
    print(f"DEBUG: Getting papers - domain: {domain}, category: {category}, days_back: {days_back}, limit: {limit}")
    
    try:
        papers = get_papers_by_domain_and_date(domain, days_back, limit, category)
        
        # Convert Paper objects to dict for JSON response
        paper_list = []
        for paper in papers:
            paper_dict = {
                'arxiv_id': paper.arxiv_id,
                'title': paper.title,
                'abstract': paper.abstract,
                'authors': paper.authors,
                'categories': paper.categories,
                'pdf_url': paper.pdf_url,
                'published_date': paper.published_date.isoformat(),
                'updated_date': paper.updated_date.isoformat()
            }
            paper_list.append(paper_dict)
        
        print(f"DEBUG: Returning {len(paper_list)} papers")
        return paper_list
        
    except Exception as e:
        print(f"ERROR: Failed to get papers - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl")
async def crawl_papers(request: dict):
    domain = request.get('domain', 'all')
    category = request.get('category')
    days_back = request.get('days_back', 7)
    limit = request.get('limit', 50)
    
    print(f"DEBUG: Crawling papers - domain: {domain}, category: {category}, days_back: {days_back}, limit: {limit}")
    
    try:
        saved_count = crawl_papers_by_domain(domain, days_back, category, limit)
        print(f"DEBUG: Crawl completed - saved {saved_count} papers")
        
        return {
            'status': 'success',
            'saved_count': saved_count,
            'domain': domain,
            'category': category,
            'days_back': days_back,
            'limit': limit
        }
        
    except Exception as e:
        print(f"ERROR: Crawling failed - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    print("DEBUG: Getting database stats")
    
    try:
        total_count = db.get_total_count()
        
        return {
            'total_count': total_count,
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR: Failed to get stats - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories():
    return {
        'computer': COMPUTER_CATEGORIES,
        'math': MATH_CATEGORIES,
        'physics': PHYSICS_CATEGORIES,
        'all': ALL_CATEGORIES
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@router.post("/papers/analyze")
async def analyze_paper(request: dict):
    """Analyze paper with LLM"""
    arxiv_id = request.get('arxiv_id')
    
    print(f"DEBUG: /papers/analyze endpoint called with arxiv_id: {arxiv_id}")
    
    if not arxiv_id:
        print("ERROR: No arxiv_id provided in request")
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    print(f"DEBUG: Looking up paper {arxiv_id} in database")
    
    paper = db.get_paper_by_id(arxiv_id)
    if not paper:
        print(f"ERROR: Paper {arxiv_id} not found in database")
        raise HTTPException(status_code=404, detail="Paper not found")
    
    print(f"DEBUG: Found paper: {paper.title[:50]}...")
    
    paper_dict = {
        'title': paper.title,
        'abstract': paper.abstract,
        'categories': paper.categories,
        'arxiv_id': paper.arxiv_id
    }
    
    print(f"DEBUG: Calling LLM summarizer for {arxiv_id}")
    analysis = llm_summarizer.summarize_paper(paper_dict)
    print(f"DEBUG: LLM analysis completed for {arxiv_id}, length: {len(analysis)}")
    
    return {
        'arxiv_id': arxiv_id,
        'analysis': analysis,
        'timestamp': datetime.now().isoformat()
    }

@router.post("/search")
async def search_papers(request: dict):
    """Search papers by query"""
    query = request.get('query', '')
    category = request.get('category')
    max_results = request.get('max_results', 10)
    
    print(f"DEBUG: Searching papers - query: {query}, category: {category}")
    
    try:
        # Simple text search in title and abstract
        papers = db.search_papers(query, category, max_results)
        
        paper_list = []
        for paper in papers:
            paper_dict = {
                'arxiv_id': paper.arxiv_id,
                'title': paper.title,
                'abstract': paper.abstract,
                'authors': paper.authors,
                'categories': paper.categories,
                'pdf_url': paper.pdf_url,
                'published_date': paper.published_date.isoformat(),
                'updated_date': paper.updated_date.isoformat()
            }
            paper_list.append(paper_dict)
        
        print(f"DEBUG: Found {len(paper_list)} papers")
        return {
            'items': paper_list,
            'count': len(paper_list),
            'query': query
        }
        
    except Exception as e:
        print(f"ERROR: Search failed - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
