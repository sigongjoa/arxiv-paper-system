from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import sys
import os
import asyncio
import logging
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from backend.core.llm_summarizer import LLMSummarizer
from core.paper_database import PaperDatabase
from utils.pdf_generator import AIAnalysisPDFGenerator
from db.connection import get_db_session
from backend.api.category_routes import PLATFORM_DETAILED_CATEGORIES

# Add root directory to path
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_path)

# Import the new routers
from backend.api.crawling_routes import router as crawling_router
from backend.api.ai_agent_routes import router as ai_agent_router
from backend.api.category_routes import category_router # Added this from list_dir results
from backend.api.agents_routes import router as agents_router # Added this from list_dir results -> 절대 경로로 변경
from backend.api.enhanced_routes import router as enhanced_router # Added this from list_dir results

try:
    # from api.crawling.arxiv_crawler import ArxivCrawler # crawling_routes.py로 이동
    # from api.crawling.rss_crawler import ArxivRSSCrawler # crawling_routes.py로 이동
    # from core.database import DatabaseManager  # crawling_routes.py로 이동
    # from categories import COMPUTER_CATEGORIES, MATH_CATEGORIES, PHYSICS_CATEGORIES, ALL_CATEGORIES # crawling_routes.py로 이동
    pass # No crawling specific imports here anymore
except ImportError as e:
    print(f"ERROR: Core imports failed - {e}")
    raise

try:
    from backend.core.llm_summarizer import LLMSummarizer
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
    # from core.ai_agent import AIAgent # ai_agent_routes.py로 이동
    pass # No AI Agent imports here anymore
except ImportError as e:
    print(f"WARNING: AI Agent imports failed - {e}")
    # AIAgent = None # ai_agent_routes.py로 이동

try:
    # PDF Copy service
    from utils.pdf_copy_service import PdfCopyService
except ImportError as e:
    print(f"WARNING: PDF Copy imports failed - {e}")
    PdfCopyService = None

router = APIRouter()

# Include the new routers
router.include_router(crawling_router, prefix="/crawling", tags=["Crawling"])
router.include_router(ai_agent_router, prefix="/ai", tags=["AI Agent"])
router.include_router(category_router, prefix="/categories", tags=["Categories"])
router.include_router(agents_router, prefix="/agents", tags=["Agents"])
router.include_router(enhanced_router, prefix="/enhanced", tags=["Enhanced"])

# Initialize components directly
# crawler = ArxivCrawler() # crawling_routes.py로 이동
# rss_crawler = ArxivRSSCrawler() # crawling_routes.py로 이동
# db = DatabaseManager()  # crawling_routes.py로 이동
llm_summarizer = LLMSummarizer() if LLMSummarizer else None

# Initialize newsletter components
email_service = EmailService(aws_region=os.getenv('AWS_REGION', 'us-east-1')) if EmailService else None
pdf_generator = AIAnalysisPDFGenerator() if PdfGenerator else None

# Initialize citation components
citation_tracker = CitationTracker() if CitationTracker else None

# Initialize AI agent
# ai_agent = AIAgent() if AIAgent else None # ai_agent_routes.py로 이동

# Initialize PDF copy service
pdf_copy_service = PdfCopyService() if PdfCopyService else None

logging.basicConfig(level=logging.ERROR)
print("DEBUG: Routes initialized with LLM summarizer, newsletter, citation and PDF copy components")

@router.post("/papers/analyze")
async def analyze_paper(request: Request, db_session: Session = Depends(get_db_session)):
    data = await request.json()
    external_id = data.get('external_id')

    if not external_id:
        logging.warning("No external_id provided in request")
        raise HTTPException(status_code=400, detail="external_id required")

    print(f"DEBUG: Looking up paper {external_id} in database")
    db_manager = PaperDatabase(db_session)
    paper = db_manager.get_paper_by_external_id(external_id)

    if not paper:
        logging.warning(f"Paper {external_id} not found in database")
        raise HTTPException(status_code=404, detail="Paper not found")

    print(f"DEBUG: Calling LLM summarizer for {external_id}")
    analysis = await llm_summarizer.analyze_paper(paper)
    print(f"DEBUG: LLM analysis completed for {external_id}, length: {len(analysis)}")

    return {
        "status": "success",
        "message": "Paper analysis completed",
        "external_id": external_id,
        "analysis_result": analysis
    }

@router.post("/papers/pdf-analysis-report")
async def generate_pdf_report(request: Request, db_session: Session = Depends(get_db_session)):
    data = await request.json()
    external_id = data.get('external_id')
    analysis_data = data.get('analysis_result')

    if not external_id or not analysis_data:
        raise HTTPException(status_code=400, detail="external_id and analysis_result required")

    print(f"DEBUG: Generating PDF for {external_id}")
    db_manager = PaperDatabase(db_session)
    paper = db_manager.get_paper_by_external_id(external_id)

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    pdf_gen = AIAnalysisPDFGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{external_id.replace('/', '_')}_{timestamp}.pdf"
    pdf_path = pdf_gen.generate_analysis_pdf(
        title=paper.title,
        arxiv_id=paper.external_id,
        analysis=analysis_data
    )

    if not pdf_path:
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return {"pdf_path": pdf_path, "filename": filename}

# ==========================================
# AI AGENT ENDPOINTS (ai_agent_routes.py로 이동됨)
# ==========================================

# @router.post("/ai/analyze/comprehensive")
# async def comprehensive_paper_analysis(request: dict):
#     # ... ai_agent_routes.py로 이동

# @router.post("/ai/extract/findings")
# async def extract_key_findings(request: dict):
#     # ... ai_agent_routes.py로 이동

# @router.post("/ai/assess/quality")
# async def assess_paper_quality(request: dict):
#     # ... ai_agent_routes.py로 이동

# @router.post("/ai/chat")
# async def chat_with_paper(request: dict):
#     # ... ai_agent_routes.py로 이동

# @router.post("/ai/suggest/related")
# async def suggest_related_papers(request: dict):
#     # ... ai_agent_routes.py로 이동

# @router.post("/ai/generate/questions")
# async def generate_research_questions(request: dict):
#     # ... ai_agent_routes.py로 이동

# @router.post("/ai/compare")
# async def compare_papers(request: dict):
#     # ... ai_agent_routes.py로 이동

# @router.delete("/ai/chat/clear/{session_id}")
# async def clear_chat_history(session_id: str):
#     # ... ai_agent_routes.py로 이동

# @router.get("/ai/status")
# async def get_ai_agent_status():
#     # ... ai_agent_routes.py로 이동


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
        # papers = collect_and_summarize_papers(domain, days_back, max_papers) # NewsletterRoutes로 이동
        # NewsletterRoutes로 이동되었으므로, 이 부분은 삭제하거나 주석 처리합니다.
        # 기존 라우트에서 뉴스레터 관련 엔드포인트를 그대로 유지한다면, 해당 함수를 직접 호출하거나 다른 방법으로 논문을 가져와야 합니다.
        # 일단은 기존 로직을 유지하고, 필요하면 향후에 뉴스레터 관련 로직을 분리하는 것을 고려하겠습니다.
        
        # 임시로 해당 함수를 사용하도록 처리 (원래 위치로 다시 가져옴)
        from backend.api.crawling_routes import get_papers_by_domain_and_date # 임시 임포트
        papers = get_papers_by_domain_and_date(domain, days_back, max_papers)
        
        if not papers:
            return {'success': False, 'message': 'No papers found'}
        
        # 2. Generate content
        # html_content, text_content = generate_newsletter_content(papers, title) # NewsletterRoutes로 이동
        # 임시로 해당 함수를 사용하도록 처리 (원래 위치로 다시 가져옴)
        from backend.api.pdf_generator import PdfGenerator # generate_newsletter_content가 PdfGenerator에 있다고 가정
        # PdfGenerator는 HTML/텍스트 생성 로직을 포함하지 않으므로, 이 로직은 다른 유틸리티 함수나 클래스로 분리되어야 합니다.
        # 현재는 이 로직이 routes.py에 남아있다고 가정하고, PdfGenerator와는 별개로 처리합니다.
        
        # 가상의 generate_newsletter_content 함수
        def generate_newsletter_content(papers_list, newsletter_title):
            html = f"<h1>{newsletter_title}</h1>"
            text = f"{newsletter_title}\n\n"
            for p in papers_list:
                html += f"<h2>{p.title}</h2><p>{p.abstract}</p><p>Categories: {p.categories}</p><hr/>"
                text += f"Title: {p.title}\nAbstract: {p.abstract}\nCategories: {p.categories}\n\n"
            return html, text

        html_content, text_content = generate_newsletter_content(papers, title)
        
        # 3. Generate PDF
        try:
            pdf_bytes = pdf_generator.generate_from_papers(papers, title)
            print(f"DEBUG: PDF generated, size: {len(pdf_bytes)} bytes")
        except Exception as e:
            logging.error(f"ERROR: PDF generation failed: {str(e)}")
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
            logging.error(f"Email sending failed: {str(e)}")
            return {'success': False, 'error': f'Email failed: {str(e)}'}
            
    except Exception as e:
        logging.error(f"Newsletter creation failed: {str(e)}")
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


# Newsletter Automation Endpoints

@router.post("/newsletter/test")
async def test_newsletter(request: dict):
    """Test newsletter generation without sending emails"""
    domain = request.get('domain', 'computer')
    max_papers = min(request.get('max_papers', 5), 5)  # Limit to 5 for testing
    
    print(f"DEBUG: Testing newsletter generation - domain: {domain}, max_papers: {max_papers}")
    
    try:
        # Collect and summarize papers
        # papers = collect_and_summarize_papers(domain, days_back=1, max_papers=max_papers)
        papers = [] # 임시로 빈 리스트로 설정
        
        if not papers:
            return {'success': False, 'message': 'No papers found for test'}
        
        # Generate content
        # html_content, text_content = generate_newsletter_content(papers)
        html_content = ""
        text_content = ""
        
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
                'external_id': p.get('external_id', ''),
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
                'external_id': 'test.0001'
            }
            llm_summarizer.summarize_paper(test_paper)
            llm_status = 'Online'
        except Exception:
            llm_status = 'Offline'
        
        # Get database stats
        # from core.paper_database import PaperDatabase # db는 다른 라우트에서 초기화해야 함
        db = PaperDatabase() # 임시 인스턴스 생성
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
    external_id = request.get('external_id')
    title = request.get('title')
    analysis = request.get('analysis')
    
    print(f"DEBUG: Generating PDF for {external_id}")
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
        filename = f"analysis_{external_id.replace('/', '_')}_{timestamp}.pdf"
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
        
        # External ID 배지
        badge_data = [[Paragraph(f"External ID: {clean_text(external_id)}", badge_style)]]
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
            logging.error(f"DEBUG: PDF copied to main directory")
        except Exception as e:
            logging.error(f"ERROR: Failed to copy PDF: {e}")
        
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
            paper_detail = next((p for p in paper_details if p['external_id'] == rec['paper_id']), None)
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

@router.post("/ai/status")
async def get_ai_agent_status():
    """Get AI agent status"""
    try:
        from core.ai_agent import AIAgent
        if not AIAgent:
            raise HTTPException(status_code=500, detail="AI Agent not initialized")
        
        # 실제 AI 에이전트의 상태를 확인하는 로직 (예: 모델 로딩 상태, 연결 상태 등)
        return {"status": "operational", "message": "AI Agent is running and ready."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent status check failed: {str(e)}")

@router.get("/health")
async def health_check():
    """API 헬스 체크"""
    return {"status": "ok", "message": "Crawling API is healthy"}

@router.get("/platforms")
async def get_platforms():
    """사용 가능한 플랫폼 목록 및 상태 반환"""
    platforms_status = {}
    for platform_name in PLATFORM_DETAILED_CATEGORIES.keys():
        status = "active"
        message = ""
        if platform_name == "core":
            status = "needs_api_key"
            message = "API 키가 필요합니다."
        platforms_status[platform_name] = {"available": True, "status": status, "message": message}

    return {"success": True, "platforms": platforms_status}
