import os
import json
import logging
from datetime import datetime

# sys.path 설정
import sys
# 현재 파일의 부모 디렉토리 (backend)를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'core')))

# core 모듈에서 필요한 클래스 임포트
from core.arxiv_api import ArxivAPI
from core.llm_summarizer import LLMSummarizer
from core.database import DatabaseManager, create_tables, SessionLocal, Paper, Base, engine
from core.config import LLM_API_URL, DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_arxiv_papers_db(category: str = "cs.AI", max_results: int = 10):
    logger.info(f"데이터베이스 초기화 및 '{category}' 카테고리 논문 {max_results}개 크롤링 시작...")

    # 테이블 생성 (이미 존재하면 무시)
    Base.metadata.drop_all(bind=engine) # 기존 테이블 삭제
    create_tables()

    logger.info(f"데이터베이스 URL: {DATABASE_URL}")
    logger.info(f"연결 시도 중: {os.path.abspath(DATABASE_URL.replace("sqlite:///", ""))}")

    arxiv_api = ArxivAPI()
    summarizer = LLMSummarizer()
    db_manager = DatabaseManager()

    try:
        papers_data = arxiv_api.search(f"cat:{category}", max_results=max_results)
        processed_count = 0

        for paper_info in papers_data:
            paper_id = paper_info.get('arxiv_id')
            if not paper_id:
                logger.warning(f"arxiv_id가 없는 논문 건너뛰기: {paper_info.get('title', '제목 없음')}")
                continue

            existing_paper = db_manager.get_paper_by_id(paper_id)
            if existing_paper:
                logger.info(f"논문이 이미 존재합니다. 건너뛰기: {paper_id}")
                continue

            try:
                # LLM을 사용한 구조화된 요약 생성
                structured_summary = summarizer.summarize_paper(paper_info)
            except Exception as e:
                logger.error(f"논문 요약 실패 ({paper_id}): {e}. 일반 요약 사용.")
                structured_summary = json.dumps({
                    "background": {"problem_definition": paper_info.get('abstract', '')[:200]},
                    "contributions": ["Abstract summary"],
                    "methodology": {"approach": "N/A", "datasets": "N/A"},
                    "results": {"key_findings": "N/A", "performance": "N/A"}
                })
            
            logger.debug(f"Summary for {paper_id}: {structured_summary[:200]}...")
            
            # authors와 categories를 JSON 문자열로 변환 (DB 저장 형식에 맞게)
            authors_json = json.dumps([author.strip() for author in paper_info.get('authors', '').split(',') if author.strip()])
            categories_json = json.dumps([cat.strip() for cat in paper_info.get('categories', '').split(',') if cat.strip()])

            paper_to_save = {
                'paper_id': paper_id,
                'platform': 'arxiv',
                'title': paper_info.get('title', ''),
                'abstract': paper_info.get('abstract', ''),
                'authors': authors_json,
                'categories': categories_json,
                'pdf_url': paper_info.get('pdf_url'),
                'published_date': datetime.fromisoformat(paper_info['published_date'].replace('Z', '+00:00')),
                'structured_summary': structured_summary,
                'created_at': datetime.now()
            }
            
            db_manager.save_paper(paper_to_save)
            processed_count += 1
            logger.info(f"✅ 논문 저장 완료: {paper_id} - {paper_info['title'][:50]}...")
            if processed_count >= max_results:
                break

        logger.info(f"✨ 데이터베이스 채우기 완료. 총 {processed_count}개 논문 처리.")

    except Exception as e:
        logger.error(f"데이터베이스 채우기 중 오류 발생: {e}", exc_info=True)

if __name__ == "__main__":
    populate_arxiv_papers_db(category="cs.CL", max_results=5) 