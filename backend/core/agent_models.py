"""AI Research Agents Database Models"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class AgentAnalysis(Base):
    """AI 에이전트 분석 결과"""
    __tablename__ = 'agent_analysis'
    
    id = Column(Integer, primary_key=True)
    paper_id = Column(String(20), ForeignKey('papers.arxiv_id'), nullable=False)
    agent_type = Column(String(50), nullable=False)  # PaperAnalysisAgent, ResearchDiscoveryAgent, etc.
    analysis_content = Column(JSON)  # 분석 결과 JSON
    confidence_score = Column(Float)
    execution_time = Column(Float)  # 실행 시간 (초)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    # paper = relationship("Paper", back_populates="agent_analyses")

class AgentWorkflow(Base):
    """AI 에이전트 워크플로 실행 기록"""
    __tablename__ = 'agent_workflows'
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(100), unique=True, nullable=False)
    workflow_type = Column(String(50), nullable=False)  # comprehensive, single_paper, discovery
    status = Column(String(20), nullable=False)  # pending, running, completed, failed
    input_data = Column(JSON)  # 입력 데이터
    results = Column(JSON)  # 최종 결과
    summary = Column(Text)  # 결과 요약
    total_execution_time = Column(Float)
    success_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 관계 설정
    tasks = relationship("AgentTask", back_populates="workflow")

class AgentTask(Base):
    """워크플로 내 개별 작업"""
    __tablename__ = 'agent_tasks'
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(100), ForeignKey('agent_workflows.workflow_id'), nullable=False)
    task_id = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    input_data = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    execution_time = Column(Float)
    progress = Column(Float, default=0.0)
    
    # 관계 설정
    workflow = relationship("AgentWorkflow", back_populates="tasks")

class ResearchRecommendation(Base):
    """연구 추천 결과"""
    __tablename__ = 'research_recommendations'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    recommended_paper_id = Column(String(20), ForeignKey('papers.arxiv_id'), nullable=False)
    relevance_score = Column(Float, nullable=False)
    semantic_similarity = Column(Float)
    recommendation_reason = Column(Text)
    user_interests = Column(JSON)  # 사용자 관심 분야
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    # recommended_paper = relationship("Paper")

class CitationRelation(Base):
    """인용 관계"""
    __tablename__ = 'citation_relations'
    
    id = Column(Integer, primary_key=True)
    citing_paper_id = Column(String(20), ForeignKey('papers.arxiv_id'), nullable=False)
    cited_paper_id = Column(String(20), nullable=False)  # 외부 논문일 수 있음
    citation_context = Column(Text)
    citation_type = Column(String(20))  # direct, indirect, comparison, extension
    confidence = Column(Float)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    # citing_paper = relationship("Paper", foreign_keys=[citing_paper_id])

class ResearchCluster(Base):
    """연구 클러스터"""
    __tablename__ = 'research_clusters'
    
    id = Column(Integer, primary_key=True)
    cluster_name = Column(String(100))
    cluster_description = Column(Text)
    keywords = Column(JSON)  # 클러스터 키워드
    paper_count = Column(Integer)
    centrality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    papers = relationship("ClusterMembership", back_populates="cluster")

class ClusterMembership(Base):
    """클러스터 멤버십"""
    __tablename__ = 'cluster_memberships'
    
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('research_clusters.id'), nullable=False)
    paper_id = Column(String(20), ForeignKey('papers.arxiv_id'), nullable=False)
    membership_score = Column(Float)  # 클러스터 소속 점수
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    cluster = relationship("ResearchCluster", back_populates="papers")
    # paper = relationship("Paper")

class AgentConfig(Base):
    """에이전트 설정"""
    __tablename__ = 'agent_configs'
    
    id = Column(Integer, primary_key=True)
    config_name = Column(String(50), unique=True, nullable=False)
    agent_type = Column(String(50), nullable=False)
    config_data = Column(JSON)  # 설정 JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemLog(Base):
    """시스템 로그"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    component = Column(String(50), nullable=False)  # agent_type or system_component
    message = Column(Text, nullable=False)
    details = Column(JSON)  # 추가 상세 정보
    execution_context = Column(JSON)  # 실행 컨텍스트
    timestamp = Column(DateTime, default=datetime.utcnow)

# 인덱스 추가 (성능 최적화)
from sqlalchemy import Index

# 자주 사용되는 쿼리를 위한 인덱스
Index('idx_agent_analysis_paper_agent', AgentAnalysis.paper_id, AgentAnalysis.agent_type)
Index('idx_agent_workflow_status', AgentWorkflow.status)
Index('idx_research_recommendations_score', ResearchRecommendation.relevance_score.desc())
Index('idx_citation_relations_citing', CitationRelation.citing_paper_id)
Index('idx_system_logs_timestamp', SystemLog.timestamp.desc())
