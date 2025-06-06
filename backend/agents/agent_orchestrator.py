"""Agent Orchestrator for AI Research System"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import time
from enum import Enum
from datetime import timedelta
from .lm_studio_client import LMStudioClient, LMStudioConfig
from .paper_analysis_agent import PaperAnalysisAgent, PaperAnalysisResult
from .research_discovery_agent import ResearchDiscoveryAgent, ResearchQuery, ResearchRecommendation
from .citation_network_agent import CitationNetworkAgent, NetworkAnalysis

# 데이터베이스 서비스 import 추가
try:
    from ..core.agent_database_service import AgentDatabaseService
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("데이터베이스 서비스를 사용할 수 없습니다. 메모리 모드로 실행합니다.")

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """워크플로 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowTask:
    """워크플로 작업"""
    task_id: str
    task_type: str
    input_data: Dict[str, Any]
    status: WorkflowStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress: float = 0.0

@dataclass
class AgentWorkflowResult:
    """에이전트 워크플로 결과"""
    workflow_id: str
    tasks: List[WorkflowTask]
    total_execution_time: float
    success_rate: float
    summary: str

class AgentOrchestrator:
    """AI 에이전트 오케스트레이터"""
    
    def __init__(self, config: Optional[LMStudioConfig] = None):
        self.config = config or LMStudioConfig()
        self.llm_client = None
        self.agents = {}
        self.active_workflows = {}
        self.task_queue = asyncio.Queue()
        self.is_running = False
        
        # 데이터베이스 서비스 초기화
        if DATABASE_AVAILABLE:
            try:
                self.db_service = AgentDatabaseService()
                logger.info("데이터베이스 서비스 초기화 완료")
            except Exception as e:
                logger.warning(f"데이터베이스 서비스 초기화 실패: {e}")
                self.db_service = None
        else:
            self.db_service = None

    async def initialize(self):
        """오케스트레이터 초기화"""
        try:
            logger.info("AI 에이전트 오케스트레이터 초기화 시작")
            start_time = time.time()
            
            # LM Studio 클라이언트 초기화
            self.llm_client = LMStudioClient(self.config)
            
            # 연결 확인
            if not self.llm_client.check_connection():
                raise Exception("LM Studio 연결 실패")
            
            # 에이전트 초기화
            await self._initialize_agents()
            
            # 작업 처리 시작
            self.is_running = True
            asyncio.create_task(self._process_task_queue())
            
            init_time = time.time() - start_time
            logger.info(f"오케스트레이터 초기화 완료 - 시간: {init_time:.2f}s")
            
        except Exception as e:
            logger.error(f"오케스트레이터 초기화 실패: {e}", exc_info=True)
            raise

    async def _initialize_agents(self):
        """에이전트들 초기화"""
        try:
            # 논문 분석 에이전트
            self.agents['PaperAnalysisAgent'] = PaperAnalysisAgent(self.llm_client)
            
            # 연구 발견 에이전트
            discovery_agent = ResearchDiscoveryAgent(self.llm_client)
            await discovery_agent.initialize_embeddings()
            self.agents['ResearchDiscoveryAgent'] = discovery_agent
            
            # 인용 네트워크 에이전트
            self.agents['CitationNetworkAgent'] = CitationNetworkAgent(self.llm_client)
            
            logger.info(f"에이전트 초기화 완료: {list(self.agents.keys())}")
            
        except Exception as e:
            logger.error(f"에이전트 초기화 실패: {e}", exc_info=True)
            raise

    async def analyze_single_paper(self, paper_content: str, paper_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """단일 논문 분석"""
        try:
            workflow_id = f"single_paper_{int(time.time())}"
            logger.info(f"단일 논문 분석 시작: {workflow_id}")
            start_time = time.time()
            
            # 데이터베이스에 워크플로 기록
            if self.db_service:
                self.db_service.save_workflow(
                    workflow_id=workflow_id,
                    workflow_type="single_paper",
                    input_data={
                        "paper_id": paper_metadata.get('id'),
                        "paper_title": paper_metadata.get('title')
                    }
                )
            
            # 논문 분석 실행
            analysis_agent = self.agents['PaperAnalysisAgent']
            analysis_result = await analysis_agent.analyze_paper(paper_content, paper_metadata)
            
            execution_time = time.time() - start_time
            
            # 데이터베이스에 분석 결과 저장
            if self.db_service and analysis_result:
                try:
                    self.db_service.save_agent_analysis(
                        paper_id=paper_metadata.get('id', ''),
                        agent_type="PaperAnalysisAgent",
                        analysis_content=asdict(analysis_result),
                        confidence_score=analysis_result.confidence_score,
                        execution_time=execution_time
                    )
                    
                    # 워크플로 완료 업데이트
                    self.db_service.update_workflow(
                        workflow_id=workflow_id,
                        status="completed",
                        results=asdict(analysis_result),
                        summary=analysis_result.summary[:200] + "..." if len(analysis_result.summary) > 200 else analysis_result.summary,
                        execution_time=execution_time,
                        success_rate=1.0
                    )
                except Exception as e:
                    logger.error(f"분석 결과 저장 실패: {e}", exc_info=True)
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'analysis': asdict(analysis_result),
                'execution_time': execution_time
            }
            
        except Exception as e:
            logger.error(f"단일 논문 분석 실패: {e}", exc_info=True)
            
            # 데이터베이스에 실패 기록
            if self.db_service:
                try:
                    self.db_service.update_workflow(
                        workflow_id=workflow_id,
                        status="failed",
                        execution_time=time.time() - start_time if 'start_time' in locals() else 0
                    )
                    
                    self.db_service.log_system_event(
                        level="ERROR",
                        component="AgentOrchestrator",
                        message=f"논문 분석 실패: {str(e)}",
                        details={
                            "workflow_id": workflow_id,
                            "paper_id": paper_metadata.get('id'),
                            "error": str(e)
                        }
                    )
                except Exception as db_error:
                    logger.error(f"실패 기록 저장 실패: {db_error}")
            
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e)
            }

    async def discover_related_research(self, query: ResearchQuery) -> Dict[str, Any]:
        """관련 연구 발견"""
        try:
            workflow_id = f"research_discovery_{int(time.time())}"
            logger.info(f"연구 발견 시작: {workflow_id}")
            
            discovery_agent = self.agents['ResearchDiscoveryAgent']
            recommendations = await discovery_agent.discover_related_papers(query)
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'recommendations': [asdict(rec) for rec in recommendations],
                'query': asdict(query)
            }
            
        except Exception as e:
            logger.error(f"연구 발견 실패: {e}", exc_info=True)
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e)
            }

    async def analyze_citation_network(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """인용 네트워크 분석"""
        try:
            workflow_id = f"citation_network_{int(time.time())}"
            logger.info(f"인용 네트워크 분석 시작: {workflow_id}")
            
            citation_agent = self.agents['CitationNetworkAgent']
            network_analysis = await citation_agent.build_citation_network(papers)
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'network_analysis': asdict(network_analysis)
            }
            
        except Exception as e:
            logger.error(f"인용 네트워크 분석 실패: {e}", exc_info=True)
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e)
            }

    async def comprehensive_research_analysis(self, papers: List[Dict[str, Any]], research_interests: List[str] = None) -> AgentWorkflowResult:
        """포괄적 연구 분석"""
        try:
            workflow_id = f"comprehensive_{int(time.time())}"
            logger.info(f"포괄적 연구 분석 시작: {workflow_id} - {len(papers)}개 논문")
            start_time = time.time()
            
            tasks = []
            
            # 1. 개별 논문 분석
            paper_analysis_tasks = []
            for i, paper in enumerate(papers[:10]):  # 최대 10개 논문
                task = WorkflowTask(
                    task_id=f"{workflow_id}_paper_{i}",
                    task_type="paper_analysis",
                    input_data={'paper': paper},
                    status=WorkflowStatus.PENDING
                )
                tasks.append(task)
                paper_analysis_tasks.append(self._execute_task(task))
            
            # 2. 연구 발견 준비
            if research_interests:
                discovery_task = WorkflowTask(
                    task_id=f"{workflow_id}_discovery",
                    task_type="research_discovery",
                    input_data={'interests': research_interests, 'papers': papers},
                    status=WorkflowStatus.PENDING
                )
                tasks.append(discovery_task)
            
            # 3. 인용 네트워크 분석
            citation_task = WorkflowTask(
                task_id=f"{workflow_id}_citation",
                task_type="citation_analysis",
                input_data={'papers': papers},
                status=WorkflowStatus.PENDING
            )
            tasks.append(citation_task)
            
            # 병렬 실행
            await asyncio.gather(*paper_analysis_tasks, return_exceptions=True)
            
            # 후속 작업들 실행
            remaining_tasks = [task for task in tasks if task.task_type != "paper_analysis"]
            await asyncio.gather(*[self._execute_task(task) for task in remaining_tasks], return_exceptions=True)
            
            # 결과 통합
            total_time = time.time() - start_time
            success_count = sum(1 for task in tasks if task.status == WorkflowStatus.COMPLETED)
            success_rate = success_count / len(tasks) if tasks else 0.0
            
            # 요약 생성
            summary = await self._generate_workflow_summary(tasks, papers)
            
            result = AgentWorkflowResult(
                workflow_id=workflow_id,
                tasks=tasks,
                total_execution_time=total_time,
                success_rate=success_rate,
                summary=summary
            )
            
            logger.info(f"포괄적 연구 분석 완료: {workflow_id} - 성공률: {success_rate:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"포괄적 연구 분석 실패: {e}", exc_info=True)
            raise

    async def _execute_task(self, task: WorkflowTask):
        """작업 실행"""
        try:
            task.status = WorkflowStatus.RUNNING
            task.start_time = time.time()
            
            if task.task_type == "paper_analysis":
                paper = task.input_data['paper']
                agent = self.agents['PaperAnalysisAgent']
                result = await agent.analyze_paper(
                    paper.get('content', ''),
                    paper
                )
                task.result = asdict(result)
                
            elif task.task_type == "research_discovery":
                interests = task.input_data['interests']
                papers = task.input_data['papers']
                
                # 인덱스 구축
                discovery_agent = self.agents['ResearchDiscoveryAgent']
                await discovery_agent.build_paper_index(papers)
                
                # 트렌드 분석
                trends = await discovery_agent.analyze_research_trends(papers)
                task.result = trends
                
            elif task.task_type == "citation_analysis":
                papers = task.input_data['papers']
                agent = self.agents['CitationNetworkAgent']
                network_analysis = await agent.build_citation_network(papers)
                task.result = asdict(network_analysis)
            
            task.status = WorkflowStatus.COMPLETED
            task.end_time = time.time()
            task.progress = 1.0
            
        except Exception as e:
            task.status = WorkflowStatus.FAILED
            task.error_message = str(e)
            task.end_time = time.time()
            logger.error(f"작업 실행 실패: {task.task_id} - {e}", exc_info=True)

    async def _generate_workflow_summary(self, tasks: List[WorkflowTask], papers: List[Dict[str, Any]]) -> str:
        """워크플로 요약 생성"""
        try:
            completed_tasks = [task for task in tasks if task.status == WorkflowStatus.COMPLETED]
            
            # 분석 결과 수집
            analysis_results = []
            for task in completed_tasks:
                if task.task_type == "paper_analysis" and task.result:
                    analysis_results.append(task.result.get('summary', ''))
            
            papers_info = f"총 {len(papers)}개 논문 분석"
            tasks_info = f"완료된 작업: {len(completed_tasks)}/{len(tasks)}"
            
            prompt = f"""다음 연구 분석 결과를 요약해주세요:

{papers_info}
{tasks_info}

주요 분석 결과:
{chr(10).join(analysis_results[:5])}

요약 요구사항:
1. 전체 분석 개요
2. 주요 발견사항
3. 연구 트렌드 및 인사이트
4. 3-4문단으로 작성

분석 요약:"""
            
            summary = await self.llm_client.generate_response(
                prompt, 
                "You are a research analysis summarizer. Provide comprehensive Korean summaries."
            )
            
            return summary or f"{papers_info} 완료. {tasks_info}"
            
        except Exception as e:
            logger.error(f"워크플로 요약 생성 실패: {e}", exc_info=True)
            return f"총 {len(papers)}개 논문에 대한 분석이 완료되었습니다."

    async def _process_task_queue(self):
        """작업 큐 처리"""
        while self.is_running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._execute_task(task)
                self.task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"작업 큐 처리 실패: {e}", exc_info=True)

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        try:
            agent_status = {}
            for name, agent in self.agents.items():
                if hasattr(agent, 'get_embedding_stats'):
                    agent_status[name] = agent.get_embedding_stats()
                elif hasattr(agent, 'get_network_stats'):
                    agent_status[name] = agent.get_network_stats()
                else:
                    agent_status[name] = {'status': 'ready'}
            
            return {
                'orchestrator_status': 'running' if self.is_running else 'stopped',
                'llm_connection': self.llm_client.check_connection() if self.llm_client else False,
                'agents': agent_status,
                'active_workflows': len(self.active_workflows),
                'available_models': self.llm_client.get_available_models() if self.llm_client else []
            }
            
        except Exception as e:
            logger.error(f"시스템 상태 조회 실패: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    async def shutdown(self):
        """오케스트레이터 종료"""
        try:
            logger.info("AI 에이전트 오케스트레이터 종료 시작")
            
            self.is_running = False
            
            # 큐의 남은 작업 완료 대기
            await self.task_queue.join()
            
            logger.info("오케스트레이터 종료 완료")
            
        except Exception as e:
            logger.error(f"오케스트레이터 종료 실패: {e}", exc_info=True)
