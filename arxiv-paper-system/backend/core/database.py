import os
import sqlite3
from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'

    paper_id = Column(String, primary_key=True, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)  # List of author names
    categories = Column(JSON, nullable=True) # List of category tags
    published_date = Column(DateTime, nullable=True)
    updated_date = Column(DateTime, nullable=True) # For tracking updates to papers

    def __repr__(self):
        return f"<Paper(paper_id='{self.paper_id}', title='{self.title[:50]}...')>"

def create_tables(engine):
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), 'arxiv_papers.db')
    engine = create_engine(f'sqlite:///{db_path}')
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