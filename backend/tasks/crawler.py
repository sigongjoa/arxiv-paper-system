from celery import Celery
from sqlalchemy.orm import sessionmaker
import logging
from core import ArxivAPI, LLMSummarizer, engine, REDIS_URL # Paper는 더 이상 직접 사용되지 않음
from .paper_processor import PaperProcessor # 새로 생성한 PaperProcessor 임포트

logger = logging.getLogger(__name__)

celery_app = Celery('arxiv_crawler', broker=REDIS_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task
def crawl_and_process_papers(category, max_results=100):
    arxiv = ArxivAPI()
    summarizer = LLMSummarizer()
    db_session = SessionLocal()
    processor = PaperProcessor(session=db_session, summarizer=summarizer)
    
    papers = arxiv.search(f"cat:{category}", max_results=max_results)
    processed_count = 0
    
    for paper_data in papers:
        if processor.process_paper(paper_data):
        processed_count += 1
    
    db_session.commit()
    db_session.close()
    
    logger.info(f"Processed {processed_count} papers")
    return {"processed": processed_count}
