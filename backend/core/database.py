import os
import sqlite3
from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from .config import Config # Config 클래스 임포트
from .models import Base, Paper # models.py에서 Base와 Paper 임포트

logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
SQLALCHEMY_DATABASE_URL = f"sqlite:///{Config.DATABASE_PATH}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables(engine):
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    db_path = Config.DATABASE_PATH # Config에서 경로 가져오기
    engine = create_engine(f'sqlite:///{db_path}') # sqlite:/// 접두사 추가
    create_tables(engine)
    logger.info(f"Database and tables created at {db_path}")

    # Example: Add a dummy paper for testing
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        new_paper = Paper(
            paper_id="2506.04226v1",
            title="Example Paper Title for RAG Test",
            abstract="This is an abstract for an example paper. It describes the content and methodology.",
            authors=["John Doe", "Jane Smith"],
            categories=["cs.AI", "cs.CL"],
            published_date=datetime.now(),
            updated_date=datetime.now()
        )
        session.add(new_paper)
        session.commit()
        logger.info(f"Added dummy paper: {new_paper.paper_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to add dummy paper: {e}")
    finally:
        session.close() 