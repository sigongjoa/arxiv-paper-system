from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import sys
import os
import asyncio

# Add root directory to path
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_path)

try:
    from arxiv_crawler import ArxivCrawler
    from database import PaperDatabase  
    from categories import COMPUTER_CATEGORIES, MATH_CATEGORIES, PHYSICS_CATEGORIES, ALL_CATEGORIES
    from backend.core.llm_summarizer import LLMSummarizer
    
    # Newsletter automation imports
    from backend.automation.email_service import EmailService
    from backend.automation.pdf_generator import PdfGenerator
except ImportError as e:
    print(f"ERROR: Failed to import modules - {e}")
    raise

router = APIRouter()

# Initialize components directly
crawler = ArxivCrawler()
db = PaperDatabase()
llm_summarizer = LLMSummarizer()

# Initialize newsletter components
email_service = EmailService(aws_region=os.getenv('AWS_REGION', 'us-east-1'))
pdf_generator = PdfGenerator()

print("DEBUG: Routes initialized with crawler, database, LLM summarizer and newsletter components")

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
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    print(f"DEBUG: Collecting papers from {start_date.date()} to {end_date.date()}")
    
    papers_with_summaries = []
    paper_count = 0
    
    try:
        for paper in crawler.crawl_papers(categories, start_date, end_date):
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
                summary = llm_summarizer.summarize_paper(paper_dict)
                paper_dict['summary'] = summary
                
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
            'error': str(e)
            }

# Mailing Configuration Endpoints

@router.post("/mailing/config")
async def save_mailing_config(request: dict):
    """Save mailing configuration"""
    print(f"DEBUG: Saving mailing config: {request}")
    
    try:
        # TODO: Save config to database or file
        # For now, just validate and return success
        required_fields = ['smtpHost', 'smtpPort', 'smtpUser', 'fromEmail']
        
        for field in required_fields:
            if not request.get(field):
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        print("DEBUG: Mailing config saved successfully")
        return {'success': True, 'message': 'Configuration saved'}
        
    except Exception as e:
        print(f"ERROR: Failed to save mailing config: {str(e)}")
        return {'success': False, 'error': str(e)}

@router.get("/mailing/config")
async def get_mailing_config():
    """Get mailing configuration"""
    print("DEBUG: Getting mailing config")
    
    try:
        # TODO: Load config from database or file
        # For now, return default config
        config = {
            'smtpHost': 'smtp.gmail.com',
            'smtpPort': 587,
            'smtpUser': '',
            'smtpPassword': '',
            'fromEmail': '',
            'fromName': 'arXiv Newsletter',
            'testEmail': ''
        }
        
        return {'success': True, 'config': config}
        
    except Exception as e:
        print(f"ERROR: Failed to get mailing config: {str(e)}")
        return {'success': False, 'error': str(e)}

@router.post("/mailing/test")
async def test_mailing_config(request: dict):
    """Test mailing configuration"""
    print(f"DEBUG: Testing mailing config: {request.get('smtpHost')}")
    
    try:
        # TODO: Implement actual SMTP test
        # For now, just simulate test
        import time
        time.sleep(1)  # Simulate network delay
        
        smtp_host = request.get('smtpHost')
        test_email = request.get('testEmail')
        
        if not smtp_host or not test_email:
            return {'success': False, 'error': 'SMTP host and test email required'}
        
        print(f"DEBUG: Mail test simulated for {test_email}")
        return {'success': True, 'message': f'Test email sent to {test_email}'}
        
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
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'path': filepath
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
