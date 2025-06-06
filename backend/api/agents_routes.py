"""AI Research Agents API Routes"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import json
import time

from ..agents import (
    AgentOrchestrator, 
    LMStudioConfig,
    ResearchQuery,
    WorkflowStatus
)

logger = logging.getLogger(__name__)

# 전역 오케스트레이터 인스턴스
orchestrator: Optional[AgentOrchestrator] = None

# API 모델 정의
class LMStudioConfigRequest(BaseModel):
    base_url: str = "http://localhost:1234/v1"
    model_name: str = "local-model"
    max_tokens: int = 2000
    temperature: float = 0.7

class PaperAnalysisRequest(BaseModel):
    paper_content: str
    paper_metadata: Dict[str, Any]

class ResearchDiscoveryRequest(BaseModel):
    query_text: str
    research_interests: List[str] = []
    exclude_papers: List[str] = []
    max_results: int = 10

class ComprehensiveAnalysisRequest(BaseModel):
    papers: List[Dict[str, Any]]
    research_interests: List[str] = []

class AgentResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

# API 라우터 생성
router = APIRouter(prefix="/api/agents", tags=["AI Research Agents"])

async def get_orchestrator() -> AgentOrchestrator:
    """오케스트레이터 인스턴스 가져오기"""
    global orchestrator
    if not orchestrator:
        raise HTTPException(status_code=503, detail="AI 에이전트 시스템이 초기화되지 않음")
    return orchestrator

@router.post("/initialize", response_model=AgentResponse)
async def initialize_agents(config: Optional[LMStudioConfigRequest] = None):
    """AI 에이전트 시스템 초기화"""
    global orchestrator
    try:
        logger.info("AI 에이전트 시스템 초기화 요청")
        start_time = time.time()
        
        # 설정 준비
        lm_config = None
        if config:
            lm_config = LMStudioConfig(
                base_url=config.base_url,
                model_name=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
        
        # 오케스트레이터 생성 및 초기화
        orchestrator = AgentOrchestrator(lm_config)
        await orchestrator.initialize()
        
        execution_time = time.time() - start_time
        
        return AgentResponse(
            success=True,
            data={
                "message": "AI 에이전트 시스템 초기화 완료",
                "config": config.dict() if config else None
            },
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"AI 에이전트 초기화 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.get("/status", response_model=AgentResponse)
async def get_system_status():
    """시스템 상태 조회"""
    try:
        if not orchestrator:
            return AgentResponse(
                success=True,
                data={"status": "not_initialized"}
            )
        
        status = orchestrator.get_system_status()
        
        return AgentResponse(
            success=True,
            data=status
        )
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.post("/analyze/paper", response_model=AgentResponse)
async def analyze_single_paper(
    request: PaperAnalysisRequest,
    orchestrator_instance: AgentOrchestrator = Depends(get_orchestrator)
):
    """단일 논문 분석"""
    try:
        logger.info(f"단일 논문 분석 요청: {request.paper_metadata.get('title', 'Unknown')}")
        start_time = time.time()
        
        result = await orchestrator_instance.analyze_single_paper(
            request.paper_content,
            request.paper_metadata
        )
        
        execution_time = time.time() - start_time
        
        return AgentResponse(
            success=True,
            data=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"논문 분석 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.post("/discover/research", response_model=AgentResponse)
async def discover_related_research(
    request: ResearchDiscoveryRequest,
    orchestrator_instance: AgentOrchestrator = Depends(get_orchestrator)
):
    """관련 연구 발견"""
    try:
        logger.info(f"연구 발견 요청: {request.query_text[:100]}...")
        start_time = time.time()
        
        query = ResearchQuery(
            query_text=request.query_text,
            research_interests=request.research_interests,
            exclude_papers=request.exclude_papers,
            max_results=request.max_results
        )
        
        result = await orchestrator_instance.discover_related_research(query)
        
        execution_time = time.time() - start_time
        
        return AgentResponse(
            success=True,
            data=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"연구 발견 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.post("/analyze/citation-network", response_model=AgentResponse)
async def analyze_citation_network(
    papers: List[Dict[str, Any]],
    orchestrator_instance: AgentOrchestrator = Depends(get_orchestrator)
):
    """인용 네트워크 분석"""
    try:
        logger.info(f"인용 네트워크 분석 요청: {len(papers)}개 논문")
        start_time = time.time()
        
        result = await orchestrator_instance.analyze_citation_network(papers)
        
        execution_time = time.time() - start_time
        
        return AgentResponse(
            success=True,
            data=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"인용 네트워크 분석 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.post("/analyze/comprehensive", response_model=AgentResponse)
async def comprehensive_research_analysis(
    request: ComprehensiveAnalysisRequest,
    background_tasks: BackgroundTasks,
    orchestrator_instance: AgentOrchestrator = Depends(get_orchestrator)
):
    """포괄적 연구 분석"""
    try:
        logger.info(f"포괄적 연구 분석 요청: {len(request.papers)}개 논문")
        start_time = time.time()
        
        result = await orchestrator_instance.comprehensive_research_analysis(
            request.papers,
            request.research_interests
        )
        
        execution_time = time.time() - start_time
        
        return AgentResponse(
            success=True,
            data={
                "workflow_id": result.workflow_id,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "status": task.status.value,
                        "progress": task.progress,
                        "execution_time": (task.end_time - task.start_time) if task.end_time and task.start_time else None
                    }
                    for task in result.tasks
                ],
                "summary": result.summary,
                "success_rate": result.success_rate,
                "total_execution_time": result.total_execution_time
            },
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"포괄적 연구 분석 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.get("/models", response_model=AgentResponse)
async def get_available_models(
    orchestrator_instance: AgentOrchestrator = Depends(get_orchestrator)
):
    """사용 가능한 LM Studio 모델 목록"""
    try:
        if not orchestrator_instance.llm_client:
            raise HTTPException(status_code=503, detail="LLM 클라이언트가 초기화되지 않음")
        
        models = orchestrator_instance.llm_client.get_available_models()
        
        return AgentResponse(
            success=True,
            data={"models": models}
        )
        
    except Exception as e:
        logger.error(f"모델 목록 조회 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.post("/test/connection", response_model=AgentResponse)
async def test_lm_studio_connection(config: LMStudioConfigRequest):
    """LM Studio 연결 테스트"""
    try:
        logger.info(f"LM Studio 연결 테스트: {config.base_url}")
        
        from ..agents.lm_studio_client import LMStudioClient, LMStudioConfig
        
        test_config = LMStudioConfig(
            base_url=config.base_url,
            model_name=config.model_name,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        
        test_client = LMStudioClient(test_config)
        connection_status = test_client.check_connection()
        
        if connection_status:
            models = test_client.get_available_models()
            return AgentResponse(
                success=True,
                data={
                    "connection": "success",
                    "available_models": models,
                    "config": config.dict()
                }
            )
        else:
            return AgentResponse(
                success=False,
                error="LM Studio 연결 실패"
            )
        
    except Exception as e:
        logger.error(f"연결 테스트 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.delete("/shutdown", response_model=AgentResponse)
async def shutdown_agents():
    """AI 에이전트 시스템 종료"""
    global orchestrator
    try:
        if orchestrator:
            await orchestrator.shutdown()
            orchestrator = None
        
        return AgentResponse(
            success=True,
            data={"message": "AI 에이전트 시스템 종료 완료"}
        )
        
    except Exception as e:
        logger.error(f"시스템 종료 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

# 디버그용 엔드포인트
@router.get("/debug/logs")
async def get_debug_logs():
    """디버그 로그 조회"""
    try:
        # 간단한 시스템 정보 반환
        debug_info = {
            "orchestrator_initialized": orchestrator is not None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": {
                "agents_module_loaded": True,
                "api_routes_active": True
            }
        }
        
        if orchestrator:
            debug_info["system_status"] = orchestrator.get_system_status()
        
        return AgentResponse(
            success=True,
            data=debug_info
        )
        
    except Exception as e:
        logger.error(f"디버그 로그 조회 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )
