import os
import sys
import logging
from datetime import datetime

# Add the isolated_test_env/backend directory to the Python path
# This allows importing modules relative to this directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir) # This is arxiv_paper_system/isolated_test_env/backend
sys.path.insert(0, parent_dir)

# Import from the isolated environment
from core.config import Config
from core.models import Paper, Base
from db.connection import engine, create_tables, SessionLocal

# Setup basic logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_db_schema_test():
    logger.info("Starting database schema test in isolated environment.")

    # Ensure the database directory exists
    os.makedirs(Config.DATABASE_DIR, exist_ok=True)
    
    # Delete existing database file to ensure a clean slate for schema creation
    db_path = Config.DATABASE_PATH
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Existing database file removed: {db_path}")

    # Create tables based on the current models.py
    create_tables()
    logger.info("Database tables created successfully.")

    # Test saving a paper with new fields
    session = SessionLocal()
    try:
        new_paper = Paper(
            paper_id="test_paper_1",
            external_id="test_external_id_1",
            platform="test_platform",
            title="Test Paper for Multi-Platform DB Schema",
            abstract="This is an abstract for a test paper to verify the new database schema with external_id and platform fields.",
            authors=["Tester One", "Tester Two"],
            categories=["cs.AI", "cs.DB"],
            pdf_url="http://test.com/test_paper_1.pdf",
            embedding=[0.1, 0.2, 0.3, 0.4], # Example embedding
            published_date=datetime.now(),
            updated_date=datetime.now()
        )
        session.add(new_paper)
        session.commit()
        session.refresh(new_paper)
        logger.info(f"Successfully saved paper: {new_paper.paper_id}")

        # Verify the saved paper
        retrieved_paper = session.query(Paper).filter_by(paper_id="test_paper_1").first()
        if retrieved_paper:
            logger.info(f"Retrieved paper: {retrieved_paper.paper_id}")
            logger.info(f"  External ID: {retrieved_paper.external_id}")
            logger.info(f"  Platform: {retrieved_paper.platform}")
            logger.info(f"  PDF URL: {retrieved_paper.pdf_url}")
            logger.info(f"  Embedding: {retrieved_paper.embedding}")
            if retrieved_paper.external_id == "test_external_id_1" and \
               retrieved_paper.platform == "test_platform" and \
               retrieved_paper.pdf_url == "http://test.com/test_paper_1.pdf" and \
               retrieved_paper.embedding == [0.1, 0.2, 0.3, 0.4]:
                logger.info("Database schema test PASSED!")
            else:
                logger.error("Database schema test FAILED: Retrieved data mismatch.")
        else:
            logger.error("Database schema test FAILED: Paper not retrieved.")

    except Exception as e:
        session.rollback()
        logger.error(f"An error occurred during database schema test: {e}", exc_info=True)
        logger.error("Database schema test FAILED!")
    finally:
        session.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    run_db_schema_test() 