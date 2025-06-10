import os
import sys
import logging
import time
from datetime import datetime, timedelta
import requests
import json

# Configure logging to output to console immediately
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Add a stream handler to ensure logs are flushed immediately to console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# Ensure LM_STUDIO_BASE_URL is set for the test environment
# In a real scenario, this would be handled by the environment or CI/CD
if "LM_STUDIO_BASE_URL" not in os.environ:
    os.environ["LM_STUDIO_BASE_URL"] = "http://127.0.0.1:1234/v1" # Explicitly set for testing
    logging.warning(f"LM_STUDIO_BASE_URL not found in environment. Setting to default: {os.environ["LM_STUDIO_BASE_URL"]}")

# Add root directory to path to allow imports from backend
current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(current_dir)
sys.path.insert(0, root_path)

# Import core components
from backend.core.paper_database import PaperDatabase
from backend.api.crawling.arxiv_crawler import ArxivCrawler
from backend.core.faiss_manager import FAISSManager
from backend.core.llm_reranker import LLMReranker
from backend.core.models import Paper # Import Paper model to ensure it's compatible

def run_integrated_test():
    logging.info("Starting integrated recommendation system test...")
    
    db_path = "test_arxiv_papers.db" # Use a separate DB for testing
    index_path = "test_arxiv_papers.faiss"

    # Clean up previous test files if they exist
    if os.path.exists(db_path):
        os.remove(db_path)
        logging.info(f"Removed old test database: {db_path}")
    if os.path.exists(index_path):
        os.remove(index_path)
        logging.info(f"Removed old FAISS index: {index_path}")
    
    paper_db = None
    faiss_manager = None
    llm_reranker = None

    try:
        # 1. Initialize Database
        paper_db = PaperDatabase(db_path=db_path)
        logging.info("PaperDatabase initialized.")

        # 2. Crawl some papers
        crawler = ArxivCrawler(delay=1.0) # Reduce delay for testing
        logging.info("ArxivCrawler initialized. Starting crawling...")

        test_category = "cs.AI" # Example category
        crawl_limit = 5 # Small limit for testing

        crawled_papers_count = 0
        for paper in crawler.crawl_papers(categories=[test_category], start_date=None, end_date=None, limit=crawl_limit):
            paper_data = {
                'paper_id': paper.paper_id,
                'platform': paper.platform,
                'title': paper.title,
                'abstract': paper.abstract,
                'authors': paper.authors,
                'categories': paper.categories,
                'pdf_url': paper.pdf_url,
                'published_date': paper.published_date,
                'updated_date': paper.updated_date,
                'embedding': paper.embedding # Ensure embedding is passed
            }
            # Use the save_paper method that accepts Paper object directly
            temp_paper_obj = Paper(**paper_data)
            if paper_db.save_paper(temp_paper_obj):
                crawled_papers_count += 1
                logging.info(f"Saved paper: {paper.title[:50]}...")
            else:
                logging.warning(f"Skipped duplicate paper: {paper.title[:50]}...")
        logging.info(f"Finished crawling. Total papers saved: {crawled_papers_count}")
        
        if crawled_papers_count == 0:
            logging.error("No papers crawled. Cannot proceed with FAISS and LLM test.")
            return

        # 3. Initialize FAISS Manager and build index
        faiss_manager = FAISSManager(db_path=db_path, index_path=index_path)
        # Ensure index is built with newly crawled papers
        faiss_manager.rebuild_index()
        logging.info("FAISSManager initialized and index rebuilt.")

        # 4. Initialize LLM Reranker
        llm_reranker = LLMReranker()
        logging.info("LLMReranker initialized.")

        # 5. Simulate recommendation request
        user_interests = ["deep learning", "natural language processing", "computer vision"]
        num_candidates = 2 # Reduce for testing LM Studio context limit
        top_k_rerank = 2 # Final recommendations after LLM re-ranking
        
        logging.info(f"Attempting to recommend papers for interests: {user_interests}")
        
        # Mimic the logic in main.py's recommend_papers endpoint
        query_text = " ".join(user_interests)
        faiss_results = faiss_manager.search_papers(query_text, k=num_candidates)

        if not faiss_results:
            logging.warning("No paper candidates found with FAISS for recommendation.")
            print("Test Failed: No FAISS candidates found.")
            return
        
        candidate_paper_ids = [pid for pid, _ in faiss_results]
        candidate_papers_full_data = []
        for paper_id in candidate_paper_ids:
            paper = paper_db.get_paper_by_id(paper_id)
            if paper:
                candidate_papers_full_data.append({
                    "paper_id": paper.paper_id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "categories": paper.categories,
                    "pdf_url": paper.pdf_url,
                    "published_date": paper.published_date.isoformat(),
                    "updated_date": paper.updated_date.isoformat(),
                })
        
        if not candidate_papers_full_data:
            logging.warning("No full paper data found for FAISS candidates.")
            print("Test Failed: No full paper data for candidates.")
            return

        try:
            logging.info("Attempting LLM re-ranking...")
            reranked_papers = llm_reranker.rerank_and_explain(
                user_interests=user_interests,
                papers=candidate_papers_full_data,
                top_k=top_k_rerank
            )
            logging.info("LLM re-ranking call completed.")

        except requests.exceptions.RequestException as req_e:
            logging.error(f"HTTP Request Error during LLM re-ranking: {req_e}")
            print(f"Test Failed: HTTP Request Error - {req_e}")
            return
        except json.JSONDecodeError as json_e:
            logging.error(f"JSON Decode Error during LLM re-ranking: {json_e}")
            print(f"Test Failed: JSON Decode Error - {json_e}")
            return
        except Exception as e:
            logging.exception("An unexpected error occurred during LLM re-ranking.")
            print(f"Test Failed: Unexpected Error during LLM re-ranking - {e}")
            return

        if reranked_papers:
            logging.info(f"Successfully received {len(reranked_papers)} recommended papers.")
            print("\n--- Recommended Papers ---")
            for i, paper in enumerate(reranked_papers):
                print(f"  {i+1}. Title: {paper.get('title')[:70]}...")
                print(f"     Score: {paper.get('llm_score'):.2f}")
                print(f"     Reason: {paper.get('llm_explanation')}")
                print(f"     PDF: {paper.get('pdf_url')}")
                print("--------------------------")
            print("Test Passed: Recommendation pipeline executed successfully.")
        else:
            logging.error("No papers recommended by LLM reranker.")
            print("Test Failed: LLM reranker returned no recommendations.")

    except Exception as e:
        logging.exception("An error occurred during the integrated test.")
        print(f"Test Failed with exception: {e}")
    finally:
        # Clean up generated test files
        if os.path.exists(db_path):
            os.remove(db_path)
            logging.info(f"Cleaned up test database: {db_path}")
        if os.path.exists(index_path):
            os.remove(index_path)
            logging.info(f"Cleaned up FAISS index: {index_path}")
        logging.info("Integrated test finished.")

if __name__ == "__main__":
    run_integrated_test() 