import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import sys
import os

# 기존 시스템 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from api.crawling.arxiv_crawler import ArxivCrawler
from backend.core.paper_database import PaperDatabase
from backend.core.llm_summarizer import LLMSummarizer

from .email_service import EmailService
from .pdf_generator import PdfGenerator
from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

class NewsletterService:
    def __init__(self, 
                 email_service: EmailService,
                 pdf_generator: PdfGenerator,
                 queue_manager: QueueManager):
        
        self.email_service = email_service
        self.pdf_generator = pdf_generator
        self.queue_manager = queue_manager
        
        # 기존 시스템 컴포넌트 초기화
        self.crawler = ArxivCrawler()
        self.db = PaperDatabase()
        self.llm_summarizer = LLMSummarizer()
        
        logger.info("DEBUG: NewsletterService initialized with existing systems")
    
    def collect_and_summarize_papers(self, 
                                   categories: List[str], 
                                   days_back: int = 1,
                                   max_papers: int = 20) -> List[Dict]:
        """논문 수집 및 LLM 요약 생성"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"DEBUG: Collecting papers from {start_date.date()} to {end_date.date()}")
        
        papers_with_summaries = []
        paper_count = 0
        
        for paper in self.crawler.crawl_papers(categories, start_date, end_date):
            if paper_count >= max_papers:
                break
                
            try:
                # Paper 객체를 딕셔너리로 변환
                paper_dict = {
                    'arxiv_id': paper.paper_id,
                    'title': paper.title,
                    'abstract': paper.abstract,
                    'authors': paper.authors,
                    'categories': paper.categories,
                    'pdf_url': paper.pdf_url,
                    'published_date': paper.published_date.isoformat() if paper.published_date else None
                }
                
                # LLM 요약 생성
                logger.info(f"DEBUG: Generating summary for {paper.paper_id}")
                summary = self.llm_summarizer.summarize_paper(paper_dict)
                paper_dict['summary'] = summary
                
                papers_with_summaries.append(paper_dict)
                paper_count += 1
                
                # DB에 저장
                self.db.save_paper(paper)
                
            except Exception as e:
                logger.error(f"ERROR: Failed to process paper {paper.paper_id}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"DEBUG: Collected and summarized {len(papers_with_summaries)} papers")
        return papers_with_summaries
    
    def create_daily_newsletter_task(self, 
                                   recipients: List[str],
                                   categories: List[str] = None,
                                   config: Dict = None) -> str:
        """일일 뉴스레터 작업 생성"""
        
        if categories is None:
            categories = ['all']  # 전체 검색
        
        # 어제 논문들 수집 및 요약
        papers = self.collect_and_summarize_papers(categories, days_back=1, max_papers=15)
        
        if not papers:
            logger.warning("DEBUG: No papers found for daily newsletter")
            return None
        
        default_config = {
            'subject': f'arXiv Daily Newsletter - {datetime.now().strftime("%Y-%m-%d")}',
            'title': 'arXiv Daily Newsletter',
            'sender_email': 'newsletter@example.com'
        }
        
        if config:
            default_config.update(config)
        
        task_id = self.create_newsletter_task(papers, recipients, default_config)
        logger.info(f"DEBUG: Daily newsletter task created: {task_id}")
        return task_id
    
    def create_newsletter_task(self, 
                             papers: List[Dict],
                             recipients: List[str],
                             config: Dict) -> str:
        
        task_id = self.queue_manager.add_newsletter_task(
            task_type='generate_newsletter',
            papers=papers,
            recipients=recipients,
            config=config
        )
        
        logger.info(f"DEBUG: Newsletter task created: {task_id}")
        return task_id
    
    async def process_newsletter_task(self, task_data: Dict) -> Dict:
        task_id = task_data['task_id']
        papers = task_data['papers']
        recipients = task_data['recipients']
        config = task_data['config']
        
        self.queue_manager.update_task_status(task_id, 'processing')
        
        try:
            # PDF 생성
            logger.info(f"DEBUG: Generating PDF for task {task_id}")
            pdf_bytes = await self.pdf_generator.generate_from_papers(
                papers=papers,
                title=config.get('title', 'arXiv Newsletter')
            )
            
            # HTML 콘텐츠 생성
            html_content = self._generate_html_content(papers, config)
            text_content = self._generate_text_content(papers, config)
            
            # 이메일 전송
            logger.info(f"DEBUG: Sending emails for task {task_id}")
            email_results = self.email_service.send_batch_emails([{
                'subject': config.get('subject', 'arXiv Newsletter'),
                'html_content': html_content,
                'text_content': text_content,
                'recipients': recipients,
                'sender_email': config.get('sender_email'),
                'pdf_attachment': pdf_bytes,
                'pdf_filename': f"arxiv_newsletter_{datetime.now().strftime('%Y%m%d')}.pdf"
            }])
            
            result = {
                'pdf_size': len(pdf_bytes),
                'emails_sent': len([r for r in email_results if r.get('success')]),
                'emails_failed': len([r for r in email_results if not r.get('success')]),
                'completed_at': datetime.now().isoformat()
            }
            
            self.queue_manager.update_task_status(task_id, 'completed', result)
            logger.info(f"DEBUG: Task completed: {task_id}")
            return result
            
        except Exception as e:
            error_result = {'error': str(e), 'failed_at': datetime.now().isoformat()}
            self.queue_manager.update_task_status(task_id, 'failed', error_result)
            logger.error(f"ERROR: Task failed {task_id}: {str(e)}", exc_info=True)
            raise
    
    def _generate_html_content(self, papers: List[Dict], config: Dict) -> str:
        title = config.get('title', 'arXiv Newsletter')
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        html = f"""
        <h1>{title}</h1>
        <p><strong>Date:</strong> {date_str}</p>
        <p><strong>Papers:</strong> {len(papers)} new papers</p>
        <hr>
        """
        
        for i, paper in enumerate(papers, 1):
            html += f"""
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
        
        return html
    
    def _generate_text_content(self, papers: List[Dict], config: Dict) -> str:
        title = config.get('title', 'arXiv Newsletter')
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        content = f"{title}\n"
        content += f"Date: {date_str}\n"
        content += f"Papers: {len(papers)} new papers\n"
        content += "=" * 50 + "\n\n"
        
        for i, paper in enumerate(papers, 1):
            content += f"{i}. {paper.get('title', 'No Title')}\n"
            content += f"Authors: {', '.join(paper.get('authors', [])[:3])}\n"
            content += f"Categories: {', '.join(paper.get('categories', []))}\n"
            content += f"arXiv ID: {paper.get('arxiv_id', 'N/A')}\n"
            content += f"Summary: {paper.get('summary', 'No summary available')}\n"
            content += f"PDF: {paper.get('pdf_url', '#')}\n"
            content += "-" * 30 + "\n\n"
        
        return content
    
    def schedule_daily_newsletter(self, 
                                time_hour: int = 9,
                                time_minute: int = 0,
                                config: Dict = None) -> str:
        
        tomorrow = datetime.now().replace(hour=time_hour, minute=time_minute, second=0, microsecond=0)
        tomorrow += timedelta(days=1)
        
        task_data = {
            'type': 'daily_newsletter',
            'config': config or {}
        }
        
        task_id = self.queue_manager.add_scheduled_task(
            task_type='daily_newsletter',
            schedule_time=tomorrow,
            task_data=task_data
        )
        
        logger.info(f"DEBUG: Daily newsletter scheduled for {tomorrow}")
        return task_id
