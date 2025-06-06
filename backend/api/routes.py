from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import sys
import os
import asyncio
import logging

# Add root directory to path
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_path)

try:
    from api.crawling.arxiv_crawler import ArxivCrawler
    from api.crawling.rss_crawler import ArxivRSSCrawler
    from core.database import DatabaseManager  # 통합
    from categories import COMPUTER_CATEGORIES, MATH_CATEGORIES, PHYSICS_CATEGORIES, ALL_CATEGORIES
except ImportError as e:
    print(f"ERROR: Core imports failed - {e}")
    raise

try:
    from core.llm_summarizer import LLMSummarizer
    from config import config_manager
except ImportError as e:
    print(f"WARNING: LLM/Config imports failed - {e}")
    LLMSummarizer = None
    config_manager = None

try:
    # Newsletter automation imports
    from automation.email_service import EmailService
    from automation.pdf_generator import PdfGenerator
except ImportError as e:
    print(f"WARNING: Newsletter imports failed - {e}")
    EmailService = None
    PdfGenerator = None

try:
    # Recommendation system imports
    from core.recommendation_engine import get_recommendation_engine
except ImportError as e:
    print(f"WARNING: Recommendation imports failed - {e}")
    get_recommendation_engine = None

try:
    # Citation tracking imports
    from citation.core.citation_tracker import CitationTracker
except ImportError as e:
    print(f"WARNING: Citation imports failed - {e}")
    CitationTracker = None

try:
    # AI Agent imports
    from core.ai_agent import AIAgent
except ImportError as e:
    print(f"WARNING: AI Agent imports failed - {e}")
    AIAgent = None

try:
    # PDF Copy service
    from utils.pdf_copy_service import PdfCopyService
except ImportError as e:
    print(f"WARNING: PDF Copy imports failed - {e}")
    PdfCopyService = None

router = APIRouter()

# Initialize components directly
crawler = ArxivCrawler()
rss_crawler = ArxivRSSCrawler()
db = DatabaseManager()  # 통합
llm_summarizer = LLMSummarizer() if LLMSummarizer else None

# Initialize newsletter components
email_service = EmailService(aws_region=os.getenv('AWS_REGION', 'us-east-1')) if EmailService else None
pdf_generator = PdfGenerator() if PdfGenerator else None

# Initialize citation components
citation_tracker = CitationTracker() if CitationTracker else None

# Initialize AI agent
ai_agent = AIAgent() if AIAgent else None

# Initialize PDF copy service
pdf_copy_service = PdfCopyService() if PdfCopyService else None

logging.basicConfig(level=logging.ERROR)
print("DEBUG: Routes initialized with crawler, RSS crawler, database, LLM summarizer, newsletter, citation and AI agent components")

def get_papers_by_domain_and_date(domain: str, days_back: int, limit: int, category: str = None):
    """Get papers by domain and date range"""
    from utils import DateCalculator
    
    # 날짜 범위 계산
    start_date, end_date = DateCalculator.calculate_range(days_back)
    
    # DB에서 날짜 범위에 맞는 논문 가져오기
    papers = db.get_papers_by_date_range(start_date, end_date, limit * 5)
    
    print(f"DEBUG: Raw papers from DB: {len(papers)}")
    if papers:
        print(f"DEBUG: Sample paper dates: {[p.created_at.isoformat() for p in papers[:3]]}")
    
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
        
        papers = [p for p in papers if any(cat in str(p.categories) for cat in filter_cats)]
    
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
    for paper in rss_crawler.crawl_papers_by_rss(categories, limit):
        if db.save_paper(paper):
            saved_count += 1
            logging.error(f"RSS saved paper: {paper.arxiv_id}")
    
    logging.error(f"RSS crawl completed: {saved_count} papers saved")
    return saved_count

def crawl_papers_by_domain(domain: str, days_back: int, category: str = None, limit: int = 50):
    """Crawl papers by domain or specific category"""
    print(f"DEBUG: crawl_papers_by_domain called with domain={domain}, days_back={days_back}, category={category}, limit={limit}")
    
    from datetime import timezone
    from utils import DateCalculator
    
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

def collect_and_summarize_papers(domain: str, days_back: int = 1, max_papers: int = 10):
    """Collect and summarize papers for newsletter"""
    # Get domain categories
    if domain.lower() == 'computer':
        categories = COMPUTER_CATEGORIES[:5]  # Limit categories for performance
    elif domain.lower() == 'math':
        categories = MATH_CATEGORIES[:5]
    elif domain.lower() == 'physics':
        categories = PHYSICS_CATEGORIES[:5]
    else:
        categories = COMPUTER_CATEGORIES[:3]  # Default
    
    from utils import DateCalculator
    start_date, end_date = DateCalculator.calculate_range(days_back)
    
    print(f"DEBUG: Collecting papers from {start_date.date()} to {end_date.date()}")
    
    papers_with_summaries = []
    paper_count = 0
    
    try:
        for paper in crawler.crawl_papers(categories, start_date, end_date, limit=max_papers):
            if paper_count >= max_papers:
                break
                
            try:
                # Paper 객체를 딕셔너리로 변환
                paper_dict = {
                    'arxiv_id': paper.arxiv_id,
                    'title': paper.title,
                    'abstract': paper.abstract,
                    'authors': paper.authors,
                    'categories': paper.categories,
                    'pdf_url': paper.pdf_url
                }
                
                # LLM 요약 생성
                print(f"DEBUG: Generating summary for {paper.arxiv_id}")
                if llm_summarizer:
                    summary = llm_summarizer.summarize_paper(paper_dict)
                    paper_dict['summary'] = summary
                else:
                    paper_dict['summary'] = "LLM summarizer not available"
                
                papers_with_summaries.append(paper_dict)
                paper_count += 1
                
                # DB에 저장
                db.save_paper(paper)
                
            except Exception as e:
                print(f"ERROR: Failed to process paper {paper.arxiv_id}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"ERROR: Failed to crawl papers: {str(e)}")
        raise
    
    print(f"DEBUG: Collected and summarized {len(papers_with_summaries)} papers")
    return papers_with_summaries

def generate_newsletter_content(papers, title="arXiv Newsletter"):
    """Generate HTML and text content for newsletter"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    html_content = f"""
    <h1>{title}</h1>
    <p><strong>Date:</strong> {date_str}</p>
    <p><strong>Papers:</strong> {len(papers)} new papers</p>
    <hr>
    """
    
    text_content = f"{title}\nDate: {date_str}\nPapers: {len(papers)} new papers\n" + "="*50 + "\n\n"
    
    for i, paper in enumerate(papers, 1):
        # HTML 버전
        html_content += f"""
        <div style="margin-bottom: 30px; padding: 15px; border-left: 3px solid #007acc;">
            <h3>{i}. {paper.get('title', 'No Title')}</h3>
            <p><strong>Authors:</strong> {', '.join(paper.get('authors', [])[:3])}
            {'...' if len(paper.get('authors', [])) > 3 else ''}</p>
            <p><strong>Categories:</strong> {', '.join(paper.get('categories', []))}</p>
            <p><strong>arXiv ID:</strong> {paper.get('arxiv_id', 'N/A')}</p>
            <p><strong>Summary:</strong> {paper.get('summary', 'No summary available')}</p>
            <p><a href="{paper.get('pdf_url', '#')}" target="_blank">View PDF</a></p>
        </div>
        """
        
        # 텍스트 버전
        text_content += f"{i}. {paper.get('title', 'No Title')}\n"
        text_content += f"Authors: {', '.join(paper.get('authors', [])[:3])}\n"
        text_content += f"Categories: {', '.join(paper.get('categories', []))}\n"
        text_content += f"arXiv ID: {paper.get('arxiv_id', 'N/A')}\n"
        text_content += f"Summary: {paper.get('summary', 'No summary available')}\n"
        text_content += f"PDF: {paper.get('pdf_url', '#')}\n"
        text_content += "-"*30 + "\n\n"
    
    return html_content, text_content

@router.get("/papers")
async def get_papers(
    domain: str = 'all',
    days_back: int = 3,
    limit: int = 50,
    category: Optional[str] = None
):
    print(f"DEBUG: Getting papers - domain: {domain}, category: {category}, days_back: {days_back}, limit: {limit}")
    
    try:
        # 메모리에서 크롤링 결과 가져오기 (새로운 크롤링 결과 우선)
        from api.memory_store import get_crawled_papers
        memory_papers = get_crawled_papers()
        
        if memory_papers:
            print(f"DEBUG: Found {len(memory_papers)} papers in memory")
            # 메모리에 플랫폼 필드 추가
            for paper in memory_papers:
                if 'platform' not in paper:
                    paper['platform'] = paper.get('platform', 'unknown')
                if 'crawled' not in paper:
                    paper['crawled'] = paper.get('updated_date', paper.get('created_at', ''))
            return memory_papers[:limit]
        
        # 메모리에 없으면 DB에서 가져오기
        print("DEBUG: No papers in memory, checking DB")
        papers = get_papers_by_domain_and_date(domain, days_back, limit, category)
        
        # Convert Paper objects to dict for JSON response
        paper_list = []
        for paper in papers:
            paper_dict = {
                'arxiv_id': paper.paper_id,
                'platform': paper.platform,
                'title': paper.title,
                'abstract': paper.abstract,
                'authors': paper.authors,
                'categories': paper.categories,
                'pdf_url': paper.pdf_url,
                'published_date': paper.published_date.isoformat() if paper.published_date else '',
                'crawled': paper.created_at.isoformat() if paper.created_at else ''
            }
            paper_list.append(paper_dict)
        
        print(f"DEBUG: Returning {len(paper_list)} papers from DB")
        return paper_list
        
    except Exception as e:
        print(f"ERROR: Failed to get papers - {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl-rss")
async def crawl_papers_rss(request: dict):
    domain = request.get('domain', 'cs')
    category = request.get('category')
    limit = request.get('limit', 50)
    
    logging.error(f"RSS crawl endpoint called: domain={domain}, category={category}, limit={limit}")
    
    try:
        saved_count = crawl_papers_by_rss(domain, category, limit)
        logging.error(f"RSS crawl completed: {saved_count} papers")
        
        return {
            'status': 'success',
            'saved_count': saved_count,
            'domain': domain,
            'category': category,
            'limit': limit,
            'method': 'RSS'
        }
        
    except Exception as e:
        logging.error(f"RSS crawl error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl")
async def crawl_papers(request: dict):
    domain = request.get('domain', 'all')
    category = request.get('category')
    days_back = request.get('days_back', 2)  # 기본값 2일로 증가 (시간대 문제 대응)
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
        
    except ValueError as e:
        print(f"ERROR: Invalid value - {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"ERROR: Crawling failed - {str(e)}")
        import traceback
        traceback.print_exc()
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

# Citation Tracking Endpoints

@router.post("/citation/extract/{arxiv_id}")
async def extract_citation_data(arxiv_id: str):
    """Extract citation data for a paper"""
    print(f"DEBUG: Extracting citation data for {arxiv_id}")
    
    try:
        result = citation_tracker.store_paper_and_citations(arxiv_id)
        print(f"DEBUG: Citation extraction result: {result}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: Citation extraction failed for {arxiv_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.get("/citation/network/{arxiv_id}")
async def get_citation_network(arxiv_id: str, depth: int = 2):
    """Get citation network for visualization"""
    print(f"DEBUG: Getting citation network for {arxiv_id}, depth: {depth}")
    
    try:
        network_data = citation_tracker.get_citation_network(arxiv_id, depth)
        print(f"DEBUG: Network data - nodes: {len(network_data.get('nodes', []))}, edges: {len(network_data.get('edges', []))}")
        
        return network_data
        
    except Exception as e:
        print(f"ERROR: Failed to get citation network for {arxiv_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"nodes": [], "edges": [], "error": str(e)}

@router.get("/citation/analysis/{arxiv_id}")
async def analyze_citation_patterns(arxiv_id: str):
    """Analyze citation patterns for a paper"""
    print(f"DEBUG: Analyzing citation patterns for {arxiv_id}")
    
    try:
        analysis = citation_tracker.analyze_citation_patterns(arxiv_id)
        
        # 유사한 논문도 함께 조회
        similar_papers = citation_tracker.find_similar_papers(arxiv_id, limit=5)
        analysis['similar_papers'] = similar_papers
        
        print(f"DEBUG: Citation analysis completed for {arxiv_id}")
        
        return analysis
        
    except Exception as e:
        print(f"ERROR: Citation analysis failed for {arxiv_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}



# Newsletter Automation Endpoints

@router.post("/newsletter/create")
async def create_newsletter(request: dict):
    """Create and send newsletter"""
    recipients = request.get('recipients', [])
    domain = request.get('domain', 'computer')
    days_back = request.get('days_back', 1)
    max_papers = request.get('max_papers', 10)
    sender_email = request.get('sender_email', 'newsletter@example.com')
    title = request.get('title', 'arXiv Newsletter')
    
    print(f"DEBUG: Creating newsletter - domain: {domain}, papers: {max_papers}, recipients: {len(recipients)}")
    
    try:
        # 1. Collect and summarize papers
        papers = collect_and_summarize_papers(domain, days_back, max_papers)
        
        if not papers:
            return {'success': False, 'message': 'No papers found'}
        
        # 2. Generate content
        html_content, text_content = generate_newsletter_content(papers, title)
        
        # 3. Generate PDF
        try:
            pdf_bytes = pdf_generator.generate_from_papers(papers, title)
            print(f"DEBUG: PDF generated, size: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"ERROR: PDF generation failed: {str(e)}")
            pdf_bytes = None
        
        # 4. Send email
        try:
            subject = f"{title} - {datetime.now().strftime('%Y-%m-%d')}"
            
            result = email_service.send_newsletter(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipients=recipients,
                sender_email=sender_email,
                pdf_attachment=pdf_bytes,
                pdf_filename=f"arxiv_newsletter_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
            
            return {
                'success': True,
                'papers_count': len(papers),
                'pdf_size': len(pdf_bytes) if pdf_bytes else 0,
                'message_id': result.get('message_id'),
                'recipients_count': len(recipients)
            }
            
        except Exception as e:
            print(f"ERROR: Email sending failed: {str(e)}")
            return {'success': False, 'error': f'Email failed: {str(e)}'}
            
    except Exception as e:
        print(f"ERROR: Newsletter creation failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@router.get("/pdf/status")
async def get_pdf_status():
    """PDF 디렉토리 상태 확인"""
    try:
        source_dir = "D:\\arxiv-paper-system\\backend\\output\\pdfs"
        target_dir = "D:\\arxiv-paper-system\\pdfs"
        
        source_files = [f for f in os.listdir(source_dir) if f.endswith('.pdf')]
        target_files = [f for f in os.listdir(target_dir) if f.endswith('.pdf')]
        
        missing_files = [f for f in source_files if f not in target_files]
        
        return {
            'source_count': len(source_files),
            'target_count': len(target_files),
            'missing_count': len(missing_files),
            'missing_files': missing_files,
            'sync_needed': len(missing_files) > 0
        }
        
    except Exception as e:
        print(f"ERROR: PDF status check failed: {str(e)}")
        return {'error': str(e)}

# ==========================================
# AI AGENT ENDPOINTS
# ==========================================

@router.post("/ai/analyze/comprehensive")
async def comprehensive_paper_analysis(request: dict):
    """종합적인 논문 분석"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        # 논문 정보 조회
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors,
            'arxiv_id': paper.arxiv_id
        }
        
        result = await ai_agent.analyze_paper_comprehensive(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        print(f"ERROR: Comprehensive analysis failed for {arxiv_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/extract/findings")
async def extract_key_findings(request: dict):
    """핵심 발견사항 추출"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors
        }
        
        result = await ai_agent.extract_key_findings(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        print(f"ERROR: Key findings extraction failed for {arxiv_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/assess/quality")
async def assess_paper_quality(request: dict):
    """논문 품질 평가"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors
        }
        
        result = await ai_agent.assess_paper_quality(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        print(f"ERROR: Quality assessment failed for {arxiv_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/chat")
async def chat_with_paper(request: dict):
    """논문과 대화형 상호작용"""
    paper_id = request.get('paper_id')
    message = request.get('message')
    session_id = request.get('session_id', 'default')
    
    if not paper_id or not message:
        raise HTTPException(status_code=400, detail="paper_id and message required")
    
    try:
        result = await ai_agent.chat_with_paper(paper_id, message, session_id)
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        print(f"ERROR: Chat interaction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/suggest/related")
async def suggest_related_papers(request: dict):
    """관련 논문 추천"""
    paper_id = request.get('paper_id')
    limit = request.get('limit', 5)
    
    if not paper_id:
        raise HTTPException(status_code=400, detail="paper_id required")
    
    try:
        result = await ai_agent.suggest_related_papers(paper_id, limit)
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        print(f"ERROR: Related papers suggestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/generate/questions")
async def generate_research_questions(request: dict):
    """연구 질문 생성"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors
        }
        
        result = await ai_agent.generate_research_questions(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        print(f"ERROR: Research questions generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/compare")
async def compare_papers(request: dict):
    """논문 비교 분석"""
    paper_ids = request.get('paper_ids', [])
    
    if not paper_ids or len(paper_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 paper_ids required")
    
    try:
        result = await ai_agent.compare_papers(paper_ids)
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        print(f"ERROR: Paper comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/ai/chat/clear/{session_id}")
async def clear_chat_history(session_id: str):
    """대화 히스토리 초기화"""
    try:
        ai_agent.clear_conversation_history(session_id)
        
        return {
            'success': True,
            'message': f'Chat history cleared for session {session_id}',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR: Failed to clear chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/status")
async def get_ai_agent_status():
    """AI 에이전트 상태 확인"""
    try:
        # LM Studio 연결 테스트
        test_paper = {
            'title': 'Test Paper for AI Agent Status Check',
            'abstract': 'This is a test abstract to verify AI agent functionality.',
            'categories': ['cs.AI'],
            'authors': ['Test Author']
        }
        
        # 간단한 분석 테스트
        test_result = await ai_agent.extract_key_findings(test_paper)
        
        status = {
            'ai_agent_status': 'Online' if 'main_findings' in test_result else 'Offline',
            'lm_studio_connection': 'Connected',
            'available_functions': [
                'comprehensive_analysis',
                'key_findings_extraction',
                'quality_assessment',
                'chat_interaction',
                'related_papers_suggestion',
                'research_questions_generation',
                'paper_comparison'
            ],
            'conversation_sessions': len(ai_agent.conversation_history),
            'timestamp': datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        print(f"ERROR: AI agent status check failed: {str(e)}")
        return {
            'ai_agent_status': 'Offline',
            'lm_studio_connection': 'Disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.post("/newsletter/test")
async def test_newsletter(request: dict):
    """Test newsletter generation without sending emails"""
    domain = request.get('domain', 'computer')
    max_papers = min(request.get('max_papers', 5), 5)  # Limit to 5 for testing
    
    print(f"DEBUG: Testing newsletter generation - domain: {domain}, max_papers: {max_papers}")
    
    try:
        # Collect and summarize papers
        papers = collect_and_summarize_papers(domain, days_back=1, max_papers=max_papers)
        
        if not papers:
            return {'success': False, 'message': 'No papers found for test'}
        
        # Generate content
        html_content, text_content = generate_newsletter_content(papers)
        
        # Test PDF generation
        try:
            pdf_bytes = pdf_generator.generate_from_papers(papers)
            pdf_size = len(pdf_bytes)
        except Exception as e:
            print(f"ERROR: PDF generation test failed: {str(e)}")
            pdf_size = 0
        
        return {
            'success': True,
            'papers_count': len(papers),
            'html_length': len(html_content),
            'text_length': len(text_content),
            'pdf_size': pdf_size,
            'papers_preview': [{
                'title': p.get('title', '')[:100] + '...' if len(p.get('title', '')) > 100 else p.get('title', ''),
                'arxiv_id': p.get('arxiv_id', ''),
                'categories': p.get('categories', [])[:3]
            } for p in papers[:3]]
        }
        
    except Exception as e:
        print(f"ERROR: Newsletter test failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@router.post("/newsletter/schedule")
async def schedule_newsletter(request: dict):
    """Schedule daily newsletter (placeholder)"""
    recipients = request.get('recipients', [])
    domain = request.get('domain', 'computer')
    hour = request.get('hour', 9)
    minute = request.get('minute', 0)
    
    print(f"DEBUG: Scheduling newsletter - domain: {domain}, time: {hour}:{minute:02d}")
    
    # This is a placeholder - in a real implementation you would use a scheduler like Celery
    return {
        'success': True,
        'message': f'Newsletter scheduled for {hour}:{minute:02d} daily',
        'domain': domain,
        'recipients_count': len(recipients)
    }

@router.get("/newsletter/scheduled")
async def get_scheduled_newsletters():
    """Get scheduled newsletters (placeholder)"""
    # Placeholder - return empty list for now
    return {
        'tasks': [],
        'count': 0
    }

@router.get("/newsletter/status")
async def get_newsletter_status():
    """Get newsletter system status"""
    try:
        # Check LLM status
        try:
            test_paper = {
                'title': 'Test Paper',
                'abstract': 'Test abstract for status check',
                'categories': ['cs.AI'],
                'arxiv_id': 'test.0001'
            }
            llm_summarizer.summarize_paper(test_paper)
            llm_status = 'Online'
        except Exception:
            llm_status = 'Offline'
        
        # Get database stats
        total_papers = db.get_total_count()
        
        return {
            'llm_status': llm_status,
            'email_status': 'Ready',
            'pdf_status': 'Ready',
            'total_papers': total_papers,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR: Status check failed: {str(e)}")
        return {
            'llm_status': 'Unknown',
            'email_status': 'Unknown',
            'pdf_status': 'Unknown',
            'total_papers': 0,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.post("/pdf/generate")
async def generate_analysis_pdf(request: dict):
    """Generate PDF from AI analysis"""
    arxiv_id = request.get('arxiv_id')
    title = request.get('title')
    analysis = request.get('analysis')
    
    print(f"DEBUG: Generating PDF for {arxiv_id}")
    print(f"DEBUG: Analysis data: {analysis[:200]}...")
    
    try:
        import os
        import json
        from datetime import datetime
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.colors import HexColor, black, white
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import PageBreak, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from fastapi.responses import FileResponse
        
        # PDF 저장 디렉토리
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'pdfs')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{arxiv_id.replace('/', '_')}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        print(f"DEBUG: Creating PDF at {filepath}")
        
        # 폰트 설정
        font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'src', 'assets', 'fonts', 'NanumGothic-Regular.ttf')
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                font_name = 'NanumGothic'
                print(f"DEBUG: NanumGothic font loaded from {font_path}")
            except Exception as e:
                print(f"DEBUG: Failed to load NanumGothic: {e}")
                font_name = 'Helvetica'
        else:
            font_name = 'Helvetica'
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        
        # 커스텀 스타일 정의
        from reportlab.lib.styles import ParagraphStyle
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor('#1f2937')
        )
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=HexColor('#1f2937')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            leading=14,
            spaceAfter=8,
            textColor=HexColor('#374151')
        )
        
        badge_style = ParagraphStyle(
            'Badge',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=9,
            alignment=TA_CENTER,
            textColor=HexColor('#6b7280')
        )
        
        story = []
        
        # 텍스트 정리 함수
        def clean_text(text):
            if not text:
                return ""
            import re
            text = re.sub(r'<[^>]+>', '', str(text))
            text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            text = text.replace('•', '\u2022')
            return text
        
        # 색상 서클 헤더 생성 함수
        def create_section_header(title, color_hex):
            header_table = Table([[
                Paragraph(f'<font color="{color_hex}">|</font> <b>{title}</b>', section_style)
            ]], colWidths=[6*inch])
            header_table.setStyle(TableStyle([
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            return header_table
        
        # 제목 및 메타데이터
        story.append(Paragraph(f"AI Analysis: {clean_text(title)}", title_style))
        story.append(Spacer(1, 0.1*inch))
        
        # ArXiv ID 배지
        badge_data = [[Paragraph(f"ArXiv ID: {clean_text(arxiv_id)}", badge_style)]]
        badge_table = Table(badge_data, colWidths=[2*inch])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#f3f4f6')),
            ('BORDER', (0,0), (-1,-1), 1, HexColor('#d1d5db')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        
        # 중앙 정렬을 위한 테이블
        center_table = Table([[badge_table]], colWidths=[6*inch])
        center_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        story.append(center_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 분석 데이터 파싱
        try:
            analysis_data = json.loads(analysis)
        except:
            analysis_data = {"content": analysis}
            
        # Problem Definition 섹션
        if 'background' in analysis_data and isinstance(analysis_data['background'], dict):
            bg = analysis_data['background']
            if 'problem_definition' in bg:
                story.append(create_section_header("Problem Definition", "#10b981"))
                
                # 내용을 배경색이 있는 박스로 표시
                content_data = [[Paragraph(clean_text(bg['problem_definition']), normal_style)]]
                content_table = Table(content_data, colWidths=[5.5*inch])
                content_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), HexColor('#f0f9ff')),
                    ('BORDER', (0,0), (-1,-1), 1, HexColor('#0ea5e9')),
                    ('LEFTPADDING', (0,0), (-1,-1), 15),
                    ('RIGHTPADDING', (0,0), (-1,-1), 15),
                    ('TOPPADDING', (0,0), (-1,-1), 12),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ]))
                story.append(content_table)
                story.append(Spacer(1, 0.2*inch))
        
        # Motivation 섹션
        if 'background' in analysis_data and isinstance(analysis_data['background'], dict):
            bg = analysis_data['background']
            if 'motivation' in bg:
                story.append(create_section_header("Motivation", "#8b5cf6"))
                story.append(Paragraph(clean_text(bg['motivation']), normal_style))
                story.append(Spacer(1, 0.2*inch))
        
        # Contributions 섹션
        if 'contributions' in analysis_data:
            story.append(create_section_header("Contributions", "#f59e0b"))
            
            contribs = analysis_data['contributions']
            if isinstance(contribs, list):
                for i, contrib in enumerate(contribs, 1):
                    contrib_text = f"<b>{i}.</b> {clean_text(contrib)}"
                    story.append(Paragraph(contrib_text, normal_style))
                    story.append(Spacer(1, 0.05*inch))
            else:
                story.append(Paragraph(clean_text(str(contribs)), normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Analysis Content 섹션
        if 'content' in analysis_data:
            story.append(create_section_header("Analysis Content", "#06b6d4"))
            story.append(Paragraph(clean_text(analysis_data['content']), normal_style))
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=8,
            alignment=TA_CENTER,
            textColor=HexColor('#9ca3af')
        )
        
        story.append(Spacer(1, 0.2*inch))
        footer_line = Table([[""]], colWidths=[6*inch])
        footer_line.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 1, HexColor('#e5e7eb')),
        ]))
        story.append(footer_line)
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("© 2024 ArXiv Paper Analysis System", footer_style))
        story.append(Paragraph("Generated with Modern PDF Format", footer_style))
        
        doc.build(story)
        
        print(f"DEBUG: PDF created successfully at {filepath}")
        
        # Copy to main pdfs directory
        try:
            pdf_copy_service.copy_new_pdfs()
            logger.error(f"DEBUG: PDF copied to main directory")
        except Exception as e:
            logger.error(f"ERROR: Failed to copy PDF: {e}")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/pdf',
            headers={"Content-Disposition": "inline"}
        )
        
    except Exception as e:
        print(f"ERROR: PDF generation failed - {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Mailing Configuration Endpoints

@router.post("/mailing/config")
async def save_mailing_config(request: dict):
    """Save mailing configuration"""
    print(f"DEBUG: Saving mailing config - Request data: {request}")
    
    try:
        required_fields = ['smtpHost', 'smtpPort', 'smtpUser', 'fromEmail']
        
        for field in required_fields:
            if not request.get(field):
                print(f"DEBUG: Missing required field: {field}")
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        # 디버그: 저장 전 데이터 확인
        print(f"DEBUG: About to save config with data: {request}")
        success = config_manager.save_mailing_config(request)
        
        if success:
            print("DEBUG: Mailing config saved successfully")
            # 저장 후 즉시 다시 읽어서 확인
            saved_config = config_manager.load_mailing_config()
            print(f"DEBUG: Verification - saved config: {saved_config}")
            return {'success': True, 'message': 'Configuration saved'}
        else:
            print("DEBUG: save_mailing_config returned False")
            return {'success': False, 'error': 'Failed to save configuration'}
        
    except Exception as e:
        print(f"ERROR: Failed to save mailing config: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@router.get("/mailing/config")
async def get_mailing_config():
    """Get mailing configuration"""
    print("DEBUG: Getting mailing config")
    
    try:
        config = config_manager.load_mailing_config()
        # Don't return password in response
        if 'smtpPassword' in config:
            config['smtpPassword'] = ''
        
        return {'success': True, 'config': config}
        
    except Exception as e:
        print(f"ERROR: Failed to get mailing config: {str(e)}")
        return {'success': False, 'error': str(e)}

@router.post("/mailing/test")
async def test_mailing_config(request: dict):
    """Test mailing configuration"""
    print(f"DEBUG: Testing mailing config: {request.get('smtpHost')}")
    
    try:
        result = config_manager.test_smtp_connection(request)
        return result
        
    except Exception as e:
        print(f"ERROR: Mail test failed: {str(e)}")
        return {'success': False, 'error': str(e)}

# PDF Management Endpoints

@router.get("/pdf/list")
async def get_pdf_list():
    """Get list of PDF files"""
    print("DEBUG: Getting PDF list")
    
    try:
        import os
        import glob
        from datetime import datetime
        
        # Look for PDF files in output directory
        pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        
        pdf_files = []
        pdf_pattern = os.path.join(pdf_dir, '*.pdf')
        
        for filepath in glob.glob(pdf_pattern):
            filename = os.path.basename(filepath)
            stat = os.stat(filepath)
            
            pdf_files.append({
                'id': filename.replace('.pdf', ''),
                'name': filename,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        # Sort by creation time, newest first
        pdf_files.sort(key=lambda x: x['created_at'], reverse=True)
        
        print(f"DEBUG: Found {len(pdf_files)} PDF files")
        return {'success': True, 'pdfs': pdf_files}
        
    except Exception as e:
        print(f"ERROR: Failed to get PDF list: {str(e)}")
        return {'success': False, 'error': str(e)}

@router.get("/pdf/download/{pdf_id}")
async def download_pdf(pdf_id: str):
    """Download PDF file"""
    print(f"DEBUG: Downloading PDF: {pdf_id}")
    
    try:
        import os
        from fastapi.responses import FileResponse
        
        pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'pdfs')
        pdf_path = os.path.join(pdf_dir, f"{pdf_id}.pdf")
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return FileResponse(
            path=pdf_path,
            filename=f"{pdf_id}.pdf",
            media_type='application/pdf'
        )
        
    except Exception as e:
        print(f"ERROR: PDF download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf/view/{pdf_id}")
async def view_pdf(pdf_id: str):
    """View PDF file in browser"""
    print(f"DEBUG: Viewing PDF: {pdf_id}")
    
    try:
        import os
        from fastapi.responses import FileResponse
        
        pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'pdfs')
        pdf_path = os.path.join(pdf_dir, f"{pdf_id}.pdf")
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            headers={"Content-Disposition": "inline"}
        )
        
    except Exception as e:
        print(f"ERROR: PDF view failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/pdf/delete/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """Delete PDF file"""
    print(f"DEBUG: Deleting PDF: {pdf_id}")
    
    try:
        import os
        
        pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'pdfs')
        pdf_path = os.path.join(pdf_dir, f"{pdf_id}.pdf")
        
        if not os.path.exists(pdf_path):
            return {'success': False, 'error': 'PDF not found'}
        
        os.remove(pdf_path)
        print(f"DEBUG: PDF deleted: {pdf_path}")
        
        return {'success': True, 'message': f'PDF {pdf_id} deleted'}
        
    except Exception as e:
        print(f"ERROR: PDF deletion failed: {str(e)}")
        return {'success': False, 'error': str(e)}

# Recommendation System Endpoints

@router.post("/recommendations/initialize")
async def initialize_recommendation_system(request: dict = {}):
    """추천 시스템 초기화"""
    force_rebuild = request.get('force_rebuild', False)
    
    print(f"DEBUG: Initializing recommendation system - force_rebuild: {force_rebuild}")
    
    try:
        rec_engine = get_recommendation_engine()
        rec_engine.initialize_system(force_rebuild=force_rebuild)
        
        return {
            'success': True,
            'message': '추천 시스템 초기화 완료',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR: Recommendation system initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@router.post("/recommendations/get")
async def get_recommendations(request: dict):
    """논문 추천 생성"""
    paper_id = request.get('paper_id')
    recommendation_type = request.get('type', 'hybrid')
    n_recommendations = request.get('n_recommendations', 10)
    
    print(f"DEBUG: Getting recommendations for paper {paper_id}, type: {recommendation_type}")
    
    if not paper_id:
        raise HTTPException(status_code=400, detail="paper_id required")
    
    try:
        rec_engine = get_recommendation_engine()
        
        if rec_engine.paper_embeddings is None:
            return {
                'error': '추천 시스템이 초기화되지 않았습니다. 먼저 시스템을 초기화해주세요.',
                'initialization_required': True
            }
        
        result = rec_engine.get_recommendations_for_paper(
            paper_id, 
            recommendation_type,
            n_recommendations
        )
        
        return result
        
    except Exception as e:
        print(f"ERROR: Failed to get recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/status")
async def get_recommendation_status():
    """추천 시스템 상태 확인"""
    try:
        rec_engine = get_recommendation_engine()
        
        status = {
            'initialized': rec_engine.paper_embeddings is not None,
            'paper_count': len(rec_engine.paper_ids) if rec_engine.paper_ids else 0,
            'faiss_index_ready': rec_engine.faiss_index is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        print(f"ERROR: Failed to get recommendation status: {str(e)}")
        return {
            'initialized': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.get("/recommendations/similar/{paper_id}")
async def get_similar_papers(paper_id: str, limit: int = 10):
    """유사 논문 검색 (빠른 콘텐츠 기반 추천)"""
    print(f"DEBUG: Getting similar papers for {paper_id}")
    
    try:
        rec_engine = get_recommendation_engine()
        
        if rec_engine.paper_embeddings is None:
            return {'error': '추천 시스템이 초기화되지 않았습니다'}
        
        recommendations = rec_engine.get_content_based_recommendations(paper_id, limit)
        
        if not recommendations:
            return {'similar_papers': [], 'count': 0}
        
        # 추천된 논문들의 상세 정보 조회
        paper_ids = [rec['paper_id'] for rec in recommendations]
        paper_details = rec_engine.get_paper_details(paper_ids)
        
        # 추천 점수와 논문 정보 결합
        result = []
        for rec in recommendations:
            paper_detail = next((p for p in paper_details if p['arxiv_id'] == rec['paper_id']), None)
            if paper_detail:
                paper_detail.update(rec)
                result.append(paper_detail)
        
        return {
            'similar_papers': result,
            'count': len(result),
            'source_paper_id': paper_id
        }
        
    except Exception as e:
        print(f"ERROR: Failed to get similar papers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations/rebuild")
async def rebuild_recommendation_index():
    """추천 인덱스 재구축"""
    print("DEBUG: Rebuilding recommendation index")
    
    try:
        rec_engine = get_recommendation_engine()
        rec_engine.initialize_system(force_rebuild=True)
        
        return {
            'success': True,
            'message': '추천 인덱스 재구축 완료',
            'paper_count': len(rec_engine.paper_ids),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR: Failed to rebuild recommendation index: {str(e)}")
        return {'success': False, 'error': str(e)}

@router.post("/pdf/sync")
async def sync_pdfs():
    """PDF 디렉토리 동기화"""
    print("DEBUG: Syncing PDF directories")
    
    try:
        copied_count = pdf_copy_service.copy_new_pdfs()
        
        return {
            'success': True,
            'copied_count': copied_count,
            'message': f'{copied_count}개 PDF 파일 동기화 완료',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR: PDF sync failed: {str(e)}")
        return {'success': False, 'error': str(e)}
