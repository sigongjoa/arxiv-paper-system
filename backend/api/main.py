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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime
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
            from core.database import DatabaseManager
            from datetime import timedelta
            db = DatabaseManager()
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
    from typing import Optional
    
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
            from core.database import DatabaseManager
            
            crawler = ArxivCrawler()
            db = DatabaseManager()
            
            count = 0
            for paper in crawler.crawl_papers([request.category] if request.category else [], None, None, request.limit):
                paper_data = {
                    'paper_id': paper.paper_id,
                    'platform': paper.platform,
                    'title': paper.title,
                    'abstract': paper.abstract,
                    'authors': paper.authors,
                    'categories': paper.categories,
                    'pdf_url': paper.pdf_url,
                    'published_date': paper.published_date,
                    'created_at': datetime.now()
                }
                db.save_paper(paper_data)
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
            from core.database import DatabaseManager
            
            rss_crawler = ArxivRSSCrawler()
            db = DatabaseManager()
            
            count = 0
            for paper in rss_crawler.crawl_papers([request.category] if request.category else [], None, None, request.limit):
                paper_data = {
                    'paper_id': paper.paper_id,
                    'platform': paper.platform,
                    'title': paper.title,
                    'abstract': paper.abstract,
                    'authors': paper.authors,
                    'categories': paper.categories,
                    'pdf_url': paper.pdf_url,
                    'published_date': paper.published_date,
                    'created_at': datetime.now()
                }
                db.save_paper(paper_data)
                count += 1
            
            return {"status": "success", "saved_count": count}
        except Exception as e:
            print(f"RSS crawl error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
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
    print("DEBUG: Enhanced FastAPI server starting up...")
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
