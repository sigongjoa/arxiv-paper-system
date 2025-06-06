"""AI Research Agents Database Service"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .database import SessionLocal, get_db
from .agent_models import (
    AgentAnalysis, AgentWorkflow, AgentTask, ResearchRecommendation,
    CitationRelation, ResearchCluster, ClusterMembership, 
    AgentConfig, SystemLog
)

logger = logging.getLogger(__name__)

class AgentDatabaseService:
    """AI 에이전트 데이터베이스 서비스"""
    
    def __init__(self):
        self.session_factory = SessionLocal

    def _get_session(self) -> Session:
        """데이터베이스 세션 가져오기"""
        return self.session_factory()

    def save_agent_analysis(self, paper_id: str, agent_type: str, 
                          analysis_content: Dict[str, Any], 
                          confidence_score: float, 
                          execution_time: float) -> Optional[int]:
        """에이전트 분석 결과 저장"""
        try:
            with self._get_session() as session:
                analysis = AgentAnalysis(
                    paper_id=paper_id,
                    agent_type=agent_type,
                    analysis_content=analysis_content,
                    confidence_score=confidence_score,
                    execution_time=execution_time
                )
                session.add(analysis)
                session.commit()
                session.refresh(analysis)
                
                logger.info(f"에이전트 분석 결과 저장 완료: {paper_id} - {agent_type}")
                return analysis.id
                
        except SQLAlchemyError as e:
            logger.error(f"에이전트 분석 결과 저장 실패: {e}", exc_info=True)
            return None

    def get_agent_analysis(self, paper_id: str, agent_type: str = None) -> List[Dict[str, Any]]:
        """에이전트 분석 결과 조회"""
        try:
            with self._get_session() as session:
                query = session.query(AgentAnalysis).filter(
                    AgentAnalysis.paper_id == paper_id
                )
                
                if agent_type:
                    query = query.filter(AgentAnalysis.agent_type == agent_type)
                
                analyses = query.order_by(AgentAnalysis.created_at.desc()).all()
                
                return [
                    {
                        'id': analysis.id,
                        'agent_type': analysis.agent_type,
                        'analysis_content': analysis.analysis_content,
                        'confidence_score': analysis.confidence_score,
                        'execution_time': analysis.execution_time,
                        'created_at': analysis.created_at.isoformat()
                    }
                    for analysis in analyses
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"에이전트 분석 결과 조회 실패: {e}", exc_info=True)
            return []

    def save_workflow(self, workflow_id: str, workflow_type: str, 
                     input_data: Dict[str, Any]) -> Optional[int]:
        """워크플로 시작 기록"""
        try:
            with self._get_session() as session:
                workflow = AgentWorkflow(
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    status='running',
                    input_data=input_data
                )
                session.add(workflow)
                session.commit()
                session.refresh(workflow)
                
                logger.info(f"워크플로 시작 기록: {workflow_id}")
                return workflow.id
                
        except SQLAlchemyError as e:
            logger.error(f"워크플로 저장 실패: {e}", exc_info=True)
            return None

    def update_workflow(self, workflow_id: str, 
                       status: str = None,
                       results: Dict[str, Any] = None,
                       summary: str = None,
                       execution_time: float = None,
                       success_rate: float = None) -> bool:
        """워크플로 업데이트"""
        try:
            with self._get_session() as session:
                workflow = session.query(AgentWorkflow).filter(
                    AgentWorkflow.workflow_id == workflow_id
                ).first()
                
                if not workflow:
                    logger.warning(f"워크플로를 찾을 수 없음: {workflow_id}")
                    return False
                
                if status:
                    workflow.status = status
                if results:
                    workflow.results = results
                if summary:
                    workflow.summary = summary
                if execution_time:
                    workflow.total_execution_time = execution_time
                if success_rate is not None:
                    workflow.success_rate = success_rate
                
                if status in ['completed', 'failed']:
                    workflow.completed_at = datetime.utcnow()
                
                session.commit()
                logger.info(f"워크플로 업데이트 완료: {workflow_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"워크플로 업데이트 실패: {e}", exc_info=True)
            return False

    def save_task(self, workflow_id: str, task_id: str, task_type: str,
                 input_data: Dict[str, Any]) -> Optional[int]:
        """작업 시작 기록"""
        try:
            with self._get_session() as session:
                task = AgentTask(
                    workflow_id=workflow_id,
                    task_id=task_id,
                    task_type=task_type,
                    status='running',
                    input_data=input_data,
                    start_time=datetime.utcnow()
                )
                session.add(task)
                session.commit()
                session.refresh(task)
                
                return task.id
                
        except SQLAlchemyError as e:
            logger.error(f"작업 저장 실패: {e}", exc_info=True)
            return None

    def update_task(self, task_id: str, 
                   status: str = None,
                   result: Dict[str, Any] = None,
                   error_message: str = None,
                   progress: float = None) -> bool:
        """작업 업데이트"""
        try:
            with self._get_session() as session:
                task = session.query(AgentTask).filter(
                    AgentTask.task_id == task_id
                ).first()
                
                if not task:
                    return False
                
                if status:
                    task.status = status
                if result:
                    task.result = result
                if error_message:
                    task.error_message = error_message
                if progress is not None:
                    task.progress = progress
                
                if status in ['completed', 'failed']:
                    task.end_time = datetime.utcnow()
                    if task.start_time:
                        task.execution_time = (task.end_time - task.start_time).total_seconds()
                
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"작업 업데이트 실패: {e}", exc_info=True)
            return False

    def save_recommendations(self, query_text: str, recommendations: List[Dict[str, Any]],
                           user_interests: List[str] = None) -> int:
        """연구 추천 결과 저장"""
        try:
            with self._get_session() as session:
                saved_count = 0
                
                for rec in recommendations:
                    recommendation = ResearchRecommendation(
                        query_text=query_text,
                        recommended_paper_id=rec.get('paper_id'),
                        relevance_score=rec.get('relevance_score', 0.0),
                        semantic_similarity=rec.get('semantic_similarity', 0.0),
                        recommendation_reason=rec.get('reason', ''),
                        user_interests=user_interests
                    )
                    session.add(recommendation)
                    saved_count += 1
                
                session.commit()
                logger.info(f"추천 결과 저장 완료: {saved_count}개")
                return saved_count
                
        except SQLAlchemyError as e:
            logger.error(f"추천 결과 저장 실패: {e}", exc_info=True)
            return 0

    def save_citation_relations(self, relations: List[Dict[str, Any]]) -> int:
        """인용 관계 저장"""
        try:
            with self._get_session() as session:
                saved_count = 0
                
                for rel in relations:
                    citation = CitationRelation(
                        citing_paper_id=rel.get('citing_paper'),
                        cited_paper_id=rel.get('cited_paper'),
                        citation_context=rel.get('citation_context', ''),
                        citation_type=rel.get('citation_type', 'direct'),
                        confidence=rel.get('confidence', 0.0)
                    )
                    session.add(citation)
                    saved_count += 1
                
                session.commit()
                logger.info(f"인용 관계 저장 완료: {saved_count}개")
                return saved_count
                
        except SQLAlchemyError as e:
            logger.error(f"인용 관계 저장 실패: {e}", exc_info=True)
            return 0

    def get_recent_workflows(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 워크플로 조회"""
        try:
            with self._get_session() as session:
                workflows = session.query(AgentWorkflow).order_by(
                    AgentWorkflow.created_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'workflow_id': wf.workflow_id,
                        'workflow_type': wf.workflow_type,
                        'status': wf.status,
                        'summary': wf.summary,
                        'execution_time': wf.total_execution_time,
                        'success_rate': wf.success_rate,
                        'created_at': wf.created_at.isoformat()
                    }
                    for wf in workflows
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"워크플로 조회 실패: {e}", exc_info=True)
            return []

    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 조회"""
        try:
            with self._get_session() as session:
                stats = {
                    'total_analyses': session.query(AgentAnalysis).count(),
                    'total_workflows': session.query(AgentWorkflow).count(),
                    'completed_workflows': session.query(AgentWorkflow).filter(
                        AgentWorkflow.status == 'completed'
                    ).count(),
                    'total_recommendations': session.query(ResearchRecommendation).count(),
                    'total_citations': session.query(CitationRelation).count()
                }
                
                # 에이전트별 분석 수
                agent_counts = session.query(
                    AgentAnalysis.agent_type,
                    session.query(AgentAnalysis).filter(
                        AgentAnalysis.agent_type == AgentAnalysis.agent_type
                    ).count().label('count')
                ).group_by(AgentAnalysis.agent_type).all()
                
                stats['agent_analysis_counts'] = {
                    agent_type: count for agent_type, count in agent_counts
                }
                
                return stats
                
        except SQLAlchemyError as e:
            logger.error(f"시스템 통계 조회 실패: {e}", exc_info=True)
            return {}

    def log_system_event(self, level: str, component: str, message: str, 
                        details: Dict[str, Any] = None) -> bool:
        """시스템 이벤트 로그"""
        try:
            with self._get_session() as session:
                log_entry = SystemLog(
                    log_level=level,
                    component=component,
                    message=message,
                    details=details
                )
                session.add(log_entry)
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"시스템 로그 저장 실패: {e}", exc_info=True)
            return False

    def cleanup_old_logs(self, days: int = 30) -> int:
        """오래된 로그 정리"""
        try:
            with self._get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                deleted_count = session.query(SystemLog).filter(
                    SystemLog.timestamp < cutoff_date
                ).delete()
                session.commit()
                
                logger.info(f"오래된 로그 정리 완료: {deleted_count}개")
                return deleted_count
                
        except SQLAlchemyError as e:
            logger.error(f"로그 정리 실패: {e}", exc_info=True)
            return 0
