from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(20), unique=True, nullable=False)
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
