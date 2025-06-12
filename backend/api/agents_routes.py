"""AI Research Agents API Routes"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import json
import time
import os

from backend.agents import LMStudioConfig, ResearchQuery, WorkflowStatus
from backend.agents.agent_orchestrator import AgentOrchestrator
from backend.core.config import Config
from backend.db.connection import get_db_session
from backend.core.database import Paper

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
    """종합 연구 분석을 시작합니다 (백그라운드 작업으로 실행)."""
    try:
        logger.info(f"종합 연구 분석 요청: {len(request.papers)}개 논문, 관심사: {request.research_interests}")
        start_time = time.time()

        # 백그라운드에서 실행될 실제 작업 함수
        async def _run_analysis():
            try:
                # WorkflowStatus를 사용 (가져왔으므로 사용 가능)
                await orchestrator_instance.run_comprehensive_analysis(
                    request.papers,
                    request.research_interests
                )
                logger.info("종합 연구 분석 백그라운드 작업 완료")
            except Exception as bg_e:
                logger.error(f"백그라운드 종합 연구 분석 실패: {bg_e}", exc_info=True)

        background_tasks.add_task(_run_analysis)

        execution_time = time.time() - start_time

        return AgentResponse(
            success=True,
            data={"message": "종합 연구 분석이 백그라운드에서 시작되었습니다.",
                  "workflow_status_check_url": f"/api/agents/status"},
            execution_time=execution_time
        )

    except Exception as e:
        logger.error(f"종합 연구 분석 시작 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.get("/models", response_model=AgentResponse)
async def get_available_models(
    orchestrator_instance: AgentOrchestrator = Depends(get_orchestrator)
):
    """사용 가능한 LLM 모델 목록 조회"""
    try:
        models = await orchestrator_instance.get_available_models()
        return AgentResponse(
            success=True,
            data={"models": models}
        )
    except Exception as e:
        logger.error(f"사용 가능한 모델 조회 실패: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.post("/test/connection", response_model=AgentResponse)
async def test_lm_studio_connection(config: LMStudioConfigRequest):
    """LM Studio 연결 테스트"""
    try:
        logger.info(f"LM Studio 연결 테스트: {config.base_url}")
        
        test_config = LMStudioConfig(
            base_url=config.base_url,
            model_name=config.model_name,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        client = LMStudioClient(config=test_config)
        
        response = await client.test_connection()
        return AgentResponse(success=True, data={"message": response})
    except Exception as e:
        logger.error(f"LM Studio 연결 테스트 실패: {e}", exc_info=True)
        return AgentResponse(success=False, error=str(e))

@router.delete("/shutdown", response_model=AgentResponse)
async def shutdown_agents(
    orchestrator_instance: AgentOrchestrator = Depends(get_orchestrator)
):
    """AI 에이전트 시스템 종료"""
    global orchestrator
    try:
        await orchestrator_instance.shutdown()
        orchestrator = None # 전역 인스턴스 초기화
        logger.info("AI 에이전트 시스템 종료 완료")
        return AgentResponse(success=True, data={"message": "AI 에이전트 시스템 종료 완료"})
    except Exception as e:
        logger.error(f"AI 에이전트 시스템 종료 실패: {e}", exc_info=True)
        return AgentResponse(success=False, error=str(e))

@router.get("/debug/logs")
async def get_debug_logs():
    """디버그 로그 조회"""
    log_file_path = "debug_log.txt"
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as f:
            logs = f.read()
        return {"logs": logs}
    return {"logs": "로그 파일 없음"}
