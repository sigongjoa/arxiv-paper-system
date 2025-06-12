import os
import sqlite3
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from .config import Config # Config 클래스 임포트
from .models import Base, Paper # models.py에서 Base와 Paper 임포트

logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정은 이제 db/connection.py에서 관리합니다.

# create_tables 함수도 db/connection.py로 이동

if __name__ == "__main__":
    # 이 부분은 독립적인 테스트/초기화 스크립트로 이동하거나, 필요시 main.py에서 호출되도록 재구성
    db_path = Config.DATABASE_PATH # Config에서 경로 가져오기
    from db.connection import engine, create_tables
    create_tables() # 테이블이 존재하지 않으면 생성
    logger.info(f"Database and tables created at {db_path}")

    # Example: Add a dummy paper for testing
    from db.connection import SessionLocal
    session = SessionLocal()

    try:
        new_paper = Paper(
            paper_id="2506.04226v1",
            external_id="2506.04226v1", # external_id 추가
            platform="arxiv", # platform 추가
            title="Example Paper Title for RAG Test",
            abstract="This is an abstract for an example paper. It describes the content and methodology.",
            authors=["John Doe", "Jane Smith"],
            categories=["cs.AI", "cs.CL"],
            pdf_url="http://example.com/2506.04226v1.pdf", # pdf_url 추가
            embedding=[0.1, 0.2, 0.3], # embedding 추가
            published_date=datetime.now(),
            updated_date=datetime.now()
        )
        session.add(new_paper)
        session.commit()
        session.refresh(new_paper) # 새로운 필드 반영을 위해 refresh 호출
        logger.info(f"Added dummy paper: {new_paper.paper_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to add dummy paper: {e}")
    finally:
        session.close() 