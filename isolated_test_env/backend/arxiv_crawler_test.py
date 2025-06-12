import os
import sys
import logging
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

# Add the isolated_test_env/backend directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.config import Config
from core.models import Paper
from db.connection import engine, create_tables, SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

def fetch_arxiv_papers(query: str, max_results: int = 2) -> list:
    """Fetch papers from arXiv API based on a query."""
    params = {
        "search_query": query,
        "max_results": max_results
    }
    logger.info(f"Fetching papers from arXiv API with query: {query}, max_results: {max_results}")
    try:
        response = requests.get(ARXIV_API_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        root = ET.fromstring(response.content)
        
        papers_data = []
        # Namespace for parsing XML
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}

        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip()
            abstract = entry.find('atom:summary', ns).text.strip()
            
            # Extract arxiv_id from id tag
            arxiv_id_full = entry.find('atom:id', ns).text
            arxiv_id = arxiv_id_full.split('/')[-1] # Extract the numeric ID part
            
            # Extract PDF URL
            pdf_link = entry.find("atom:link[@title='pdf']", ns)
            pdf_url = pdf_link.attrib['href'] if pdf_link is not None else None

            published_date_str = entry.find('atom:published', ns).text
            published_date = datetime.strptime(published_date_str, '%Y-%m-%dT%H:%M:%SZ')
            
            updated_date_str = entry.find('atom:updated', ns).text
            updated_date = datetime.strptime(updated_date_str, '%Y-%m-%dT%H:%M:%SZ')

            authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
            categories = [category.attrib['term'] for category in entry.findall('arxiv:category', ns)]
            
            papers_data.append({
                "paper_id": arxiv_id, # Use arxiv_id as paper_id for now
                "external_id": arxiv_id,
                "platform": "arxiv",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": categories,
                "pdf_url": pdf_url,
                "embedding": [0.0] * 768, # Mock embedding for now
                "published_date": published_date,
                "updated_date": updated_date
            })
        logger.info(f"Successfully fetched {len(papers_data)} papers from arXiv API.")
        return papers_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from arXiv API: {e}")
        return []
    except ET.ParseError as e:
        logger.error(f"Error parsing XML from arXiv API: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during API fetch: {e}", exc_info=True)
        return []

def save_papers_to_db(papers_data: list):
    """Save fetched papers to the database."""
    session = SessionLocal()
    try:
        saved_count = 0
        for data in papers_data:
            # Ensure paper_id is unique, use external_id as paper_id for simplicity
            existing_paper = session.query(Paper).filter_by(paper_id=data['paper_id']).first()
            if existing_paper:
                logger.warning(f"Paper with ID {data['paper_id']} already exists. Skipping.")
                continue

            new_paper = Paper(
                paper_id=data['paper_id'],
                external_id=data['external_id'],
                platform=data['platform'],
                title=data['title'],
                abstract=data['abstract'],
                authors=data['authors'],
                categories=data['categories'],
                pdf_url=data['pdf_url'],
                embedding=data['embedding'],
                published_date=data['published_date'],
                updated_date=data['updated_date']
            )
            session.add(new_paper)
            saved_count += 1
        session.commit()
        logger.info(f"Successfully saved {saved_count} new papers to the database.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving papers to database: {e}", exc_info=True)
    finally:
        session.close()

def run_real_crawling_test():
    logger.info("Starting real crawling test in isolated environment.")

    # Ensure a clean database for the test
    db_path = Config.DATABASE_PATH
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Existing database file removed for clean test: {db_path}")
    
    create_tables()
    logger.info("Database tables recreated for crawling test.")

    # Perform real crawling from arXiv
    arxiv_papers = fetch_arxiv_papers("LLM", max_results=3) # Fetch 3 papers about "LLM"
    if arxiv_papers:
        logger.info(f"Fetched {len(arxiv_papers)} papers from arXiv. Saving to DB...")
        # Log fetched data for verification
        for p_data in arxiv_papers:
            logger.info(f"  Fetched: Title='{p_data['title'][:50]}...', ID='{p_data['external_id']}', Platform='{p_data['platform']}'")
        save_papers_to_db(arxiv_papers)

        # Verify data in DB
        session = SessionLocal()
        retrieved_count = session.query(Paper).count()
        logger.info(f"Total papers in DB after crawl: {retrieved_count}")
        
        # Log retrieved data for verification
        retrieved_papers = session.query(Paper).limit(5).all()
        for p in retrieved_papers:
            logger.info(f"  DB Retrieved: Title='{p.title[:50]}...', ID='{p.external_id}', Platform='{p.platform}', PDF='{p.pdf_url}'")

        session.close()
        logger.info("Real crawling test completed successfully!")
    else:
        logger.error("Failed to fetch papers from arXiv API. Real crawling test FAILED.")

if __name__ == "__main__":
    run_real_crawling_test() 