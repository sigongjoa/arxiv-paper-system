import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.config import Config
from backend.core.models import Base

# 데이터베이스 연결 설정
SQLALCHEMY_DATABASE_URL = f"sqlite:///{Config.DATABASE_PATH}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(engine) 