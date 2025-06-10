from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.models import Paper
from core.llm_summarizer import LLMSummarizer

logger = logging.getLogger(__name__)

class PaperProcessor:
    def __init__(self, session: Session, summarizer: LLMSummarizer):
        self.session = session
        self.summarizer = summarizer

    def process_paper(self, paper_data: dict) -> bool:
        """단일 논문을 처리(요약 및 저장)합니다."""
        try:
            # 1. 기존 논문인지 확인
            existing_paper = self.session.query(Paper).filter_by(paper_id=paper_data['arxiv_id']).first()
            if existing_paper:
                logger.warning(f"Paper {paper_data['arxiv_id']} already exists. Skipping.")
                return False

            # 2. 논문 요약
            summary = self.summarizer.summarize_paper(paper_data)

            # 3. Paper 객체 생성
            paper = Paper(
                paper_id=paper_data['arxiv_id'],
                title=paper_data['title'],
                abstract=paper_data['abstract'],
                authors=paper_data['authors'],
                categories=paper_data['categories'],
                pdf_url=paper_data['pdf_url'],
                published_date=datetime.fromisoformat(paper_data['published_date'].replace('Z', '+00:00')),
                updated_date=datetime.now(),
                # embedding은 나중에 추가될 수 있으므로 일단 None
                embedding=None
            )

            # 4. 데이터베이스에 추가
            self.session.add(paper)
            logger.info(f"Added paper {paper.paper_id} to session.")
            return True
        except IntegrityError:
            logger.warning(f"IntegrityError: Paper {paper_data['arxiv_id']} already exists. Skipping.")
            self.session.rollback()
            return False
        except Exception as e:
            logger.error(f"Error processing paper {paper_data.get('arxiv_id', 'unknown')}: {e}", exc_info=True)
            self.session.rollback()
            return False 