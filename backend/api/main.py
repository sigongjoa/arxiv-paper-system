import sys
import os
from dotenv import load_dotenv

# Add root directory to path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_path)

# Load environment variables
env_path = os.path.join(os.path.dirname(root_path), '.env')
print(f"DEBUG: Loading env from: {env_path}")
load_dotenv(env_path)
print(f"DEBUG: EMAIL_TEST_MODE = {os.getenv('EMAIL_TEST_MODE')}")

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from api.routes import router
try:
    from api.enhanced_routes import router as enhanced_router
    enhanced_routes_available = True
except ImportError as e:
    print(f"WARNING: Enhanced routes not available: {e}")
    enhanced_routes_available = False

try:
    from api.test_routes import test_router
    test_routes_available = True
except ImportError as e:
    print(f"WARNING: Test routes not available: {e}")
    test_routes_available = False

try:
    from api.multi_platform_routes import multi_router
    multi_platform_available = True
except ImportError as e:
    print(f"ERROR: Multi-platform routes FAILED: {e}")
    import traceback
    traceback.print_exc()
    multi_platform_available = False

try:
    from api.agents_routes import router as agents_router
    agents_routes_available = True
except ImportError as e:
    print(f"WARNING: AI Agents routes not available: {e}")
    agents_routes_available = False

try:
    from api.category_routes import category_router
    category_routes_available = True
except ImportError as e:
    print(f"WARNING: Category routes not available: {e}")
    category_routes_available = False

from core.faiss_manager import FAISSManager
from core.paper_database import PaperDatabase
from core.models import Paper
from core.llm_reranker import LLMReranker

faiss_manager: Optional[FAISSManager] = None
llm_reranker: Optional[LLMReranker] = None

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Enhanced arXiv Paper Analysis System")

# Static files
try:
    static_path = os.path.join(os.path.dirname(root_path), "templates", "static")
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")
except Exception as e:
    print(f"WARNING: Static files not mounted: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")
if enhanced_routes_available:
    app.include_router(enhanced_router, prefix="/api/enhanced")
    print("DEBUG: Enhanced routes loaded successfully")
else:
    print("DEBUG: Running in legacy mode without enhanced features")

if test_routes_available:
    app.include_router(test_router, prefix="/api/test")
    print("DEBUG: Test routes loaded successfully")

if multi_platform_available:
    app.include_router(multi_router, prefix="/api/v1/multi")
    print("DEBUG: Multi-platform routes loaded successfully")

    # 추가 논문 조회 API
    @app.get("/api/v1/papers")
    async def get_papers(domain: str = "all", days_back: int = 1, limit: int = 50):
        """논문 조회 API"""
        try:
            from core.paper_database import PaperDatabase
            from datetime import timedelta
            db = PaperDatabase()
            papers = db.get_papers_by_date_range(datetime.now() - timedelta(days=days_back), datetime.now(), limit)
            result = []
            for p in papers:
                result.append({
                    "title": getattr(p, 'title', ''),
                    "paper_id": getattr(p, 'paper_id', '') or getattr(p, 'arxiv_id', ''),
                    "platform": getattr(p, 'platform', 'arxiv'),
                    "authors": getattr(p, 'authors', '').split(',') if getattr(p, 'authors', '') else [],
                    "categories": getattr(p, 'categories', '').split(',') if getattr(p, 'categories', '') else [],
                    "published_date": getattr(p, 'published_date', '').strftime('%Y-%m-%d') if getattr(p, 'published_date', None) else 'Unknown',
                    "pdf_url": getattr(p, 'pdf_url', ''),
                    "abstract": getattr(p, 'abstract', ''),
                    "created_at": getattr(p, 'created_at', '').strftime('%Y-%m-%d %H:%M:%S') if getattr(p, 'created_at', None) else 'Unknown'
                })
            return result
        except Exception as e:
            print(f"Papers API error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # 기본 크롤링 API
    from pydantic import BaseModel
    
    class CrawlRequest(BaseModel):
        domain: str
        category: Optional[str] = None
        days_back: int = 0
        limit: int = 50
    
    @app.post("/api/v1/crawl")
    async def crawl_papers(request: CrawlRequest):
        """기본 arXiv 크롤링"""
        try:
            from api.crawling.arxiv_crawler import ArxivCrawler
            from core.paper_database import PaperDatabase
            
            crawler = ArxivCrawler()
            db = PaperDatabase()
            
            count = 0
            for paper in crawler.crawl_papers([request.category] if request.category else [], None, None, request.limit):
                db.save_paper(paper)
                count += 1
            
            return {"status": "success", "saved_count": count}
        except Exception as e:
            print(f"Crawl error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    @app.post("/api/v1/crawl-rss")
    async def crawl_rss(request: CrawlRequest):
        """RSS 크롤링"""
        try:
            from api.crawling.rss_crawler import ArxivRSSCrawler
            from core.paper_database import PaperDatabase
            
            rss_crawler = ArxivRSSCrawler()
            db = PaperDatabase()
            
            count = 0
            for paper in rss_crawler.crawl_papers([request.category] if request.category else [], None, None, request.limit):
                db.save_paper(paper)
                count += 1
            
            return {"status": "success", "saved_count": count}
        except Exception as e:
            print(f"RSS crawl error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    # FAISS 기반 논문 검색 API
    @app.get("/api/v1/search_papers_faiss")
    async def search_papers_faiss(query: str = Query(..., min_length=3), k: int = Query(10, ge=1, le=100)):
        """FAISS를 사용하여 논문 검색"""
        global faiss_manager
        if faiss_manager is None:
            raise HTTPException(status_code=503, detail="FAISS manager not initialized.")

        try:
            search_results = faiss_manager.search_papers(query, k)
            paper_db = PaperDatabase()
            results = []
            for paper_id, distance in search_results:
                paper = paper_db.get_paper_by_id(paper_id)
                if paper:
                    results.append({
                        "title": paper.title,
                        "paper_id": paper.paper_id,
                        "platform": paper.platform,
                        "authors": paper.authors,
                        "categories": paper.categories,
                        "pdf_url": paper.pdf_url,
                        "abstract": paper.abstract,
                        "published_date": paper.published_date.strftime('%Y-%m-%d'),
                        "updated_date": paper.updated_date.strftime('%Y-%m-%d'),
                        "distance": float(distance) # FAISS distance
                    })
            return {"status": "success", "results": results}
        except Exception as e:
            print(f"FAISS search error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"FAISS search failed: {e}")

    # 논문 추천 API (FAISS + LLM 재랭크)
    @app.get("/api/v1/recommend_papers")
    async def recommend_papers(
        user_interests: List[str] = Query(..., description="사용자 관심사 (키워드 목록)"),
        num_candidates: int = Query(500, ge=50, le=1000, description="FAISS에서 가져올 논문 후보 수"),
        top_k_rerank: int = Query(50, ge=5, le=500, description="LLM 재랭크 후 반환할 최종 논문 수")
    ):
        """FAISS와 LLM을 사용하여 논문 추천 및 설명 생성"""
        global faiss_manager, llm_reranker
        if faiss_manager is None:
            raise HTTPException(status_code=503, detail="FAISS manager not initialized.")
        if llm_reranker is None:
            raise HTTPException(status_code=503, detail="LLM reranker not initialized. Check LM_STUDIO_BASE_URL environment variable.")

        try:
            # 1. FAISS를 이용한 후보 생성 (사용자 관심사 텍스트로 검색)
            # FAISS는 텍스트 쿼리를 임베딩하여 유사한 논문을 찾음
            query_text = " ".join(user_interests) # 사용자 관심사 키워드를 하나의 쿼리 문자열로 결합
            faiss_results = faiss_manager.search_papers(query_text, k=num_candidates)

            if not faiss_results:
                return {"status": "success", "message": "No paper candidates found with FAISS.", "results": []}
            
            # 2. 후보 논문 데이터베이스에서 세부 정보 가져오기
            paper_db = PaperDatabase()
            candidate_papers_full_data = []
            for paper_id, _ in faiss_results:
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
                return {"status": "success", "message": "No full paper data found for candidates.", "results": []}

            # 3. LLM을 이용한 재랭크 및 설명 생성
            reranked_papers = llm_reranker.rerank_and_explain(
                user_interests=user_interests,
                papers=candidate_papers_full_data,
                top_k=top_k_rerank
            )

            # 4. 최종 결과 반환
            final_recommendations = []
            for paper in reranked_papers:
                final_recommendations.append({
                    "title": paper.get("title"),
                    "paper_id": paper.get("paper_id"),
                    "platform": paper.get("platform"),
                    "authors": paper.get("authors"),
                    "categories": paper.get("categories"),
                    "pdf_url": paper.get("pdf_url"),
                    "published_date": paper.get("published_date"),
                    "abstract": paper.get("abstract"),
                    "llm_score": paper.get("llm_score"),
                    "llm_explanation": paper.get("llm_explanation")
                })

            return {"status": "success", "results": final_recommendations}
        except Exception as e:
            print(f"Recommend papers API error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Paper recommendation failed: {e}")

else:
    print("DEBUG: Multi-platform crawling not available")

if agents_routes_available:
    app.include_router(agents_router)
    print("DEBUG: AI Agents routes loaded successfully")
else:
    print("DEBUG: AI Agents not available")

if category_routes_available:
    app.include_router(category_router, prefix="/api/v1")
    print("DEBUG: Category routes loaded successfully")

@app.on_event("startup")
async def startup_event():
    global faiss_manager, llm_reranker
    print("DEBUG: Enhanced FastAPI server starting up...")
    try:
        faiss_manager = FAISSManager()
        print("DEBUG: FAISS Manager initialized.")
    except Exception as e:
        print(f"ERROR: Failed to initialize FAISS Manager: {e}")
        import traceback
        traceback.print_exc()

    try:
        lm_studio_base_url = os.getenv("LM_STUDIO_BASE_URL")
        if not lm_studio_base_url:
            print("WARNING: LM_STUDIO_BASE_URL environment variable not set. LLM Reranker will not be initialized.")
        else:
            llm_reranker = LLMReranker(lm_studio_base_url=lm_studio_base_url)
            print("DEBUG: LLM Reranker initialized for LM Studio.")
    except Exception as e:
        print(f"ERROR: Failed to initialize LLM Reranker: {e}")
        import traceback
        traceback.print_exc()
    
    if enhanced_routes_available:
        print("DEBUG: LM Studio integration enabled")
        print("DEBUG: AI agents initialized")
        print("DEBUG: Enhanced citation analysis available")
    else:
        print("DEBUG: Running in legacy mode")
        print("DEBUG: To enable enhanced features, install additional dependencies")

@app.get("/", response_class=HTMLResponse)
async def main_page():
    """멀티플랫폼 크롤링 시스템 메인 페이지"""
    try:
        template_path = os.path.join(os.path.dirname(root_path), "templates", "enhanced_crawling_system.html")
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h1>크롤링 시스템</h1><p>템플릿 로드 오류: {e}</p>"

@app.get("/legacy")
async def root():
    return {
        "message": "Enhanced arXiv Paper Analysis System",
        "version": "2.0",
        "features": [
            "AI-powered paper analysis",
            "Smart citation intelligence", 
            "Research assistant chatbot",
            "Enhanced recommendation system",
            "Automated documentation"
        ]
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Import diagnostic function
        from utils.debug_framework import run_system_diagnostics
        
        diagnostics = await run_system_diagnostics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_diagnostics": diagnostics,
            "api_status": "operational"
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "api_status": "operational"
        }

@app.get("/test")
async def test():
    """Test endpoint to check if server is running"""
    import sys
    return {
        "status": "ok",
        "python_version": sys.version,
        "current_time": datetime.now().isoformat(),
        "environment": {
            "EMAIL_TEST_MODE": os.getenv("EMAIL_TEST_MODE"),
            "AWS_REGION": os.getenv("AWS_REGION"),
            "LLM_API_URL": os.getenv("LLM_API_URL", "http://localhost:1234/v1/chat/completions")
        },
        "enhanced_features": {
            "lm_studio_integration": enhanced_routes_available,
            "ai_agents": enhanced_routes_available,
            "citation_intelligence": enhanced_routes_available,
            "debug_framework": enhanced_routes_available
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
