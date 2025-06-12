from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import Paper
from backend.db.connection import engine, create_tables # SQLAlchemy engine과 create_tables 함수 임포트
import logging

logger = logging.getLogger(__name__)

class PaperDatabase:
    def __init__(self):
        # 데이터베이스 파일 경로 설정은 database.py의 Config에서 관리되므로 여기서는 제거
        # init_db는 create_tables 함수가 대신하므로 제거
        # create_tables() # 테이블이 존재하지 않으면 생성 - main.py의 startup_event에서 호출
        logger.info("PaperDatabase initialized with SQLAlchemy.")
    
    def get_session(self) -> Session:
        SessionLocal = Session(bind=engine)
        return SessionLocal
    
    def save_paper(self, paper: Paper) -> bool:
        """논문 저장, 중복시 False 반환"""
        session = self.get_session()
        try:
            session.add(paper)
            session.commit()
            session.refresh(paper)
            logger.info(f"Saved paper: {paper.paper_id}")
            return True
        except IntegrityError:
            session.rollback()
            logger.warning(f"Skipped duplicate paper: {paper.paper_id}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving paper {paper.paper_id}: {e}")
            return False
        finally:
            session.close()
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """ID로 논문 조회"""
        session = self.get_session()
        try:
            return session.query(Paper).filter_by(paper_id=paper_id).first()
        finally:
            session.close()
    
    def get_papers_by_date_range(self, start_date: datetime, end_date: datetime, limit: Optional[int] = None) -> List[Paper]:
        """날짜 범위로 논문 조회"""
        session = self.get_session()
        try:
            query = session.query(Paper)
            query = query.filter(Paper.updated_date.between(start_date, end_date))
            query = query.order_by(Paper.updated_date.desc())
            if limit is not None:
                query = query.limit(limit)

            papers = query.all()
            logger.info(f"DB returned {len(papers)} papers for date range {start_date} to {end_date}")
        
            # 전체 논문 수도 확인 (디버깅 목적)
            total_count = session.query(Paper).count()
            logger.info(f"Total papers in DB: {total_count}")
        
            # 최근 3개 논문의 날짜 확인 (디버깅 목적)
            recent_papers = session.query(Paper).order_by(Paper.updated_date.desc()).limit(3).all()
            logger.info(f"Recent papers (top 3): {[p.paper_id for p in recent_papers]}")

            return papers
        finally:
            session.close()
    
    def get_all_papers(self, limit: Optional[int] = None) -> List[Paper]:
        """모든 논문을 최신 업데이트 날짜 기준으로 조회"""
        session = self.get_session()
        try:
            query = session.query(Paper)
            query = query.order_by(Paper.updated_date.desc())
            if limit is not None:
                query = query.limit(limit)
            papers = query.all()
            logger.info(f"DB returned {len(papers)} all papers (limit={limit})")
            return papers
        finally:
            session.close()
    
    def search_papers(self, query: str, category: str = None, limit: int = 100) -> List[Paper]:
        """제목/초록으로 논문 검색"""
        session = self.get_session()
        try:
            search_query = f"%{query}%"
            query_obj = session.query(Paper).filter(
                (Paper.title.like(search_query)) | (Paper.abstract.like(search_query))
            )

            if category:
                category_search = f"%\"%s\"%" % category # JSONB like for array
                query_obj = query_obj.filter(Paper.categories.like(category_search))
            
            query_obj = query_obj.order_by(Paper.updated_date.desc()).limit(limit)
            return query_obj.all()
        finally:
            session.close()
    
    def get_total_count(self) -> int:
        """총 논문 수"""
        session = self.get_session()
        try:
            return session.query(Paper).count()
        finally:
            session.close()
