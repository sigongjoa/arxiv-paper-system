"""기본 테스트"""
from fastapi import APIRouter

test_router = APIRouter(prefix="/test")

@test_router.get("/simple")
async def simple_test():
    return {"status": "ok", "message": "basic test works"}

@test_router.post("/crawl-test")  
async def crawl_test(request: dict):
    return {"received": request, "status": "received"}
