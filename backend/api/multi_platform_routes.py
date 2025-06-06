"""멀티플랫폼 크롤링 라우트"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

try:
    from api.crawling.working_multi_platform_crawler import WorkingMultiPlatformCrawlerAPI as MultiPlatformCrawlerAPI
    logger.error("Using working multi-platform crawler")
except ImportError as e:
    logger.error(f"Fallback to simple crawler due to import error: {e}")
    try:
        from api.crawling.multi_platform_crawler import MultiPlatformCrawlerAPI
    except ImportError:
        from api.crawling.simple_multi_platform_crawler import SimpleMultiPlatformCrawlerAPI as MultiPlatformCrawlerAPI

multi_router = APIRouter()

try:
    multi_crawler = MultiPlatformCrawlerAPI()
    logger.error("Multi-platform crawler API initialized")
except Exception as e:
    logger.error(f"Multi-platform crawler initialization failed: {e}", exc_info=True)
    multi_crawler = None

class MultiPlatformCrawlRequest(BaseModel):
    platforms: List[str]
    categories: Optional[List[str]] = None
    limit_per_platform: int = 20

@multi_router.get("/platforms")
async def GetPlatforms():
    """사용 가능한 플랫폼 목록"""
    if not multi_crawler:
        raise HTTPException(status_code=500, detail="Multi-crawler not initialized")
    
    try:
        return multi_crawler.GetAvailablePlatforms()
    except Exception as e:
        logger.error(f"GetPlatforms error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@multi_router.post("/multi-crawl")
async def StartMultiPlatformCrawl(request: MultiPlatformCrawlRequest):
    """멀티플랫폼 크롤링 시작"""
    if not multi_crawler:
        raise HTTPException(status_code=500, detail="Multi-crawler not initialized")
    
    try:
        result = multi_crawler.StartMultiPlatformCrawl(
            request.platforms,
            request.categories,
            request.limit_per_platform
        )
        return result
    except Exception as e:
        logger.error(f"MultiPlatformCrawl error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@multi_router.get("/crawling-status")
async def GetCrawlingStatus():
    """크롤링 시스템 상태"""
    if not multi_crawler:
        raise HTTPException(status_code=500, detail="Multi-crawler not initialized")
    
    try:
        return multi_crawler.GetCrawlingStatus()
    except Exception as e:
        logger.error(f"GetCrawlingStatus error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
