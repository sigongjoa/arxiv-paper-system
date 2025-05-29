from celery import Celery
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from core import ArxivAPI, LLMSummarizer, Paper, engine, REDIS_URL

logger = logging.getLogger(__name__)

celery_app = Celery('arxiv_crawler', broker=REDIS_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task
def crawl_and_process_papers(category, max_results=100):
    arxiv = ArxivAPI()
    summarizer = LLMSummarizer()
    db = SessionLocal()
    
    papers = arxiv.search(f"cat:{category}", max_results=max_results)
    processed_count = 0
    
    for paper_data in papers:
        existing = db.query(Paper).filter_by(arxiv_id=paper_data['arxiv_id']).first()
        if existing:
            continue
        
        summary = summarizer.summarize_paper(paper_data)
        
        paper = Paper(
            arxiv_id=paper_data['arxiv_id'],
            title=paper_data['title'],
            abstract=paper_data['abstract'],
            authors=paper_data['authors'],
            categories=paper_data['categories'],
            pdf_url=paper_data['pdf_url'],
            published_date=datetime.fromisoformat(paper_data['published_date'].replace('Z', '+00:00')),
            structured_summary=summary,
            created_at=datetime.now()
        )
        
        db.add(paper)
        processed_count += 1
    
    db.commit()
    db.close()
    
    logger.info(f"Processed {processed_count} papers")
    return {"processed": processed_count}
