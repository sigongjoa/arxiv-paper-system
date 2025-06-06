from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True)
    paper_id = Column(String(50), unique=True, nullable=False)
    platform = Column(String(20), nullable=False, default='arxiv')
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    authors = Column(Text)
    categories = Column(Text)
    pdf_url = Column(Text)
    published_date = Column(DateTime)
    structured_summary = Column(Text)
    created_at = Column(DateTime)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseManager:
    def __init__(self):
        create_tables()
        
    def save_paper(self, paper_data):
        import logging
        from sqlalchemy.exc import SQLAlchemyError, IntegrityError
        db = SessionLocal()
        try:
            # 중복 체크
            existing = db.query(Paper).filter(Paper.paper_id == paper_data['paper_id']).first()
            if existing:
                logging.error(f"Paper already exists: {paper_data['paper_id']}")
                return existing
            
            paper = Paper(**paper_data)
            db.add(paper)
            db.commit()
            logging.error(f"Paper saved successfully: {paper_data['paper_id']}")
            return paper
        except IntegrityError as e:
            db.rollback()
            logging.error(f"Duplicate paper detected: {paper_data.get('paper_id', 'unknown')}")
            return None
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"SQLAlchemy error saving paper {paper_data.get('paper_id', 'unknown')}: {e}")
            return None
        except Exception as e:
            db.rollback()
            logging.error(f"Unexpected error saving paper {paper_data.get('paper_id', 'unknown')}: {e}")
            return None
        finally:
            db.close()
            
    def get_papers_by_date_range(self, start_date, end_date, limit=100):
        """날짜 범위로 논문 조회"""
        from datetime import datetime
        import logging
        db = SessionLocal()
        try:
            logging.error(f"DB query range: {start_date.isoformat()} to {end_date.isoformat()}")
            
            query = db.query(Paper).filter(
                Paper.created_at >= start_date,
                Paper.created_at <= end_date
            ).order_by(Paper.created_at.desc()).limit(limit)
            
            papers = query.all()
            logging.error(f"DB returned {len(papers)} papers")
            
            # 전체 논문 수도 확인
            total_count = db.query(Paper).count()
            logging.error(f"Total papers in DB: {total_count}")
            
            # 최근 3개 논문의 날짜 확인
            recent_papers = db.query(Paper).order_by(Paper.created_at.desc()).limit(3).all()
            recent_info = [(p.paper_id, p.created_at.isoformat()) for p in recent_papers]
            logging.error(f"Recent papers: {recent_info}")
            
            return papers
        except Exception as e:
            logging.error(f"get_papers_by_date_range failed: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()
            
    def get_total_count(self):
        db = SessionLocal()
        try:
            return db.query(Paper).count()
        finally:
            db.close()
    
    def get_paper_by_id(self, paper_id: str):
        """텍정 ID로 논문 조회"""
        db = SessionLocal()
        try:
            paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()
            return paper
        finally:
            db.close()
    
    def search_papers(self, query: str, category: str = None, limit: int = 100):
        """제목/초록으로 논문 검색"""
        db = SessionLocal()
        try:
            query_filter = db.query(Paper).filter(
                (Paper.title.contains(query)) | (Paper.abstract.contains(query))
            )
            
            if category:
                query_filter = query_filter.filter(Paper.categories.contains(category))
            
            papers = query_filter.order_by(Paper.created_at.desc()).limit(limit).all()
            return papers
        finally:
            db.close()
