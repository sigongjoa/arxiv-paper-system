"""Research Discovery Agent for arXiv Research System"""

import logging
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import time
from sentence_transformers import SentenceTransformer
import faiss
from .lm_studio_client import LMStudioClient
from ..core.database import Paper  # Paper 모델 임포트
from arxiv_paper_system.backend.core.config import Config
from ..core.recommendation_engine import ModernRecommendationEngine
from ..utils.summarizer import TextSummarizer
from ..utils.html_parser import parse_html_content
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class ResearchRecommendation:
    """연구 추천 결과"""
    paper_id: str
    title: str
    relevance_score: float
    reason: str
    semantic_similarity: float

@dataclass
class ResearchQuery:
    """연구 쿼리"""
    query_text: str
    research_interests: List[str]
    exclude_papers: List[str] = None
    max_results: int = 10

class ResearchDiscoveryAgent:
    """연구 발견 AI 에이전트"""
    
    def __init__(self, llm_client: LMStudioClient):
        self.llm_client = llm_client
        self.embedding_model = None
        self.paper_index = None
        self.paper_metadata = {}
        self.system_prompt = """You are an expert research discovery assistant.
Your task is to analyze research queries and recommend relevant papers.
Always respond in Korean with detailed explanations."""

    async def initialize_embeddings(self):
        """임베딩 모델 초기화"""
        try:
            logger.info("임베딩 모델 로딩 중...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("임베딩 모델 초기화 완료")
        except Exception as e:
            logger.error(f"임베딩 모델 초기화 실패: {e}", exc_info=True)
            raise

    async def build_paper_index(self, papers: List[Dict[str, Any]]):
        """논문 인덱스 구축"""
        try:
            logger.info(f"논문 인덱스 구축 시작: {len(papers)}개 논문")
            start_time = time.time()
            
            if not self.embedding_model:
                await self.initialize_embeddings()
            
            # 텍스트 준비
            texts = []
            for paper in papers:
                text = f"{paper.get('title', '')} {paper.get('abstract', '')} {' '.join(paper.get('keywords', []))}"
                texts.append(text)
                self.paper_metadata[paper['id']] = paper
            
            # 임베딩 생성
            embeddings = self.embedding_model.encode(texts)
            
            # FAISS 인덱스 구축
            dimension = embeddings.shape[1]
            self.paper_index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
            
            # 정규화 후 추가
            faiss.normalize_L2(embeddings)
            self.paper_index.add(embeddings.astype('float32'))
            
            build_time = time.time() - start_time
            logger.info(f"논문 인덱스 구축 완료 - 시간: {build_time:.2f}s, 차원: {dimension}")
            
        except Exception as e:
            logger.error(f"논문 인덱스 구축 실패: {e}", exc_info=True)
            raise

    async def discover_related_papers(self, query: ResearchQuery) -> List[ResearchRecommendation]:
        """관련 논문 발견"""
        try:
            logger.info(f"연구 발견 시작: {query.query_text[:100]}...")
            start_time = time.time()
            
            if not self.paper_index:
                logger.warning("논문 인덱스가 없음. 빈 결과 반환")
                return []
            
            # 쿼리 임베딩 생성
            enhanced_query = await self._enhance_query(query)
            query_embedding = self.embedding_model.encode([enhanced_query])
            faiss.normalize_L2(query_embedding)
            
            # 유사 논문 검색
            similarities, indices = self.paper_index.search(
                query_embedding.astype('float32'), 
                min(query.max_results * 2, 50)  # 필터링을 위해 더 많이 검색
            )
            
            # 결과 처리
            recommendations = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if idx == -1:  # 유효하지 않은 인덱스
                    continue
                    
                paper_id = list(self.paper_metadata.keys())[idx]
                paper = self.paper_metadata[paper_id]
                
                # 제외 논문 필터링
                if query.exclude_papers and paper_id in query.exclude_papers:
                    continue
                
                # 추천 이유 생성
                reason = await self._generate_recommendation_reason(
                    query, paper, similarity
                )
                
                recommendation = ResearchRecommendation(
                    paper_id=paper_id,
                    title=paper.get('title', ''),
                    relevance_score=float(similarity),
                    reason=reason,
                    semantic_similarity=float(similarity)
                )
                
                recommendations.append(recommendation)
                
                if len(recommendations) >= query.max_results:
                    break
            
            # 관련성 점수로 재정렬
            recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            
            discovery_time = time.time() - start_time
            logger.info(f"연구 발견 완료 - 시간: {discovery_time:.2f}s, 결과: {len(recommendations)}개")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"연구 발견 실패: {e}", exc_info=True)
            return []

    async def _enhance_query(self, query: ResearchQuery) -> str:
        """쿼리 향상"""
        try:
            interests_text = ', '.join(query.research_interests) if query.research_interests else ''
            
            prompt = f"""다음 연구 쿼리를 더 구체적이고 검색에 최적화된 형태로 확장해주세요:

원본 쿼리: {query.query_text}
연구 관심사: {interests_text}

확장 요구사항:
1. 관련 기술 용어 추가
2. 동의어 및 관련어 포함
3. 영문 키워드 포함
4. 한 문단으로 작성

확장된 쿼리:"""
            
            enhanced = await self.llm_client.generate_response(prompt, self.system_prompt)
            return enhanced or query.query_text
            
        except Exception as e:
            logger.error(f"쿼리 향상 실패: {e}", exc_info=True)
            return query.query_text

    async def _generate_recommendation_reason(self, 
                                           query: ResearchQuery, 
                                           paper: Dict[str, Any], 
                                           similarity: float) -> str:
        """추천 이유 생성"""
        try:
            logging.info(f"_generate_recommendation_reason 호출됨. 쿼리: {query}, 관련 논문: {paper.get('title', '없음')}")

            prompt_messages = [
                {
                    "role": "system",
                    "content": "너는 유능한 AI 논문 추천 시스템 에이전트이다. 사용자 쿼리와 관련 논문 정보를 바탕으로 왜 이 논문이 관련성이 높은지 300자 내외로 간결하게 설명해야 한다. 설명은 명확하고 이해하기 쉬워야 하며, 기술적인 용어는 최소화해야 한다."
                },
                {
                    "role": "user",
                    "content": f"사용자 쿼리: {query.query_text}\n\n추천 논문 제목: {paper.get('title', '없음')}\n추천 논문 초록: {paper.get('abstract', '')[:300]}\n\n이 논문이 사용자 쿼리에 왜 관련성이 높은지 300자 내외로 설명해주세요."
                }
            ]
            response_content = await self.llm_client.generate_response(
                prompt="", # 실제 프롬프트는 messages 안에 있음
                messages=prompt_messages # chat/completions 엔드포인트에 메시지 목록 전달
            )
            
            return response_content
            
        except Exception as e:
            logging.error(f"추천 이유 생성 실패: {e}", exc_info=True)
            return "추천 이유를 생성할 수 없습니다."

    async def generate_research_suggestions(self, papers: List[Dict[str, Any]]) -> List[str]:
        """논문 목록에서 연구 제안 생성"""
        if not papers:
            return []
        
        paper_titles = "\n- " + "\n- ".join([p.get('title', '제목 없음') for p in papers])
        
        prompt = f"""다음 논문 제목들을 바탕으로, 해당 논문들이 시사하는 주요 연구 방향 또는 잠재적 연구 제안 3-5가지를 한국어로 간결하게 요약해주세요. 각 제안은 50자 이내로 작성하고, 번호가 매겨진 목록으로 제시해주세요.\n\n논문 제목 목록:\n{paper_titles}\n\n연구 제안:"""
        
        try:
            suggestions_text = await self.llm_client.generate_response(
                prompt,
                system_message="너는 논문들을 분석하여 새로운 연구 제안을 도출하는 유능한 연구 비서이다."
            )
            return [s.strip() for s in suggestions_text.split('\n') if s.strip()]
        except Exception as e:
            logger.error(f"연구 제안 생성 실패: {e}", exc_info=True)
            return []

    async def analyze_research_trends(self, papers: List[Dict[str, Any]], time_window: str = "6months") -> Dict[str, Any]:
        """논문 목록에서 연구 동향 분석"""
        if not papers:
            return {"error": "논문 데이터가 없습니다.", "trends": [], "keywords": []}
        
        # 예시: LLM을 사용하여 동향 분석 요약
        titles_abstracts = "\n".join([
            f"제목: {p.get('title', '')}\n초록: {p.get('abstract', '')[:200]}...\n"
            for p in papers
        ])
        
        prompt = f"""최근 {time_window} 동안의 다음 논문들에서 나타나는 주요 연구 동향 3가지와 핵심 키워드 5가지를 한국어로 요약해주세요. 동향은 번호가 매겨진 목록으로, 키워드는 쉼표로 구분된 목록으로 제시해주세요.\n\n논문 데이터:\n{titles_abstracts}\n\n연구 동향 및 키워드:"""
        
        try:
            analysis_text = await self.llm_client.generate_response(
                prompt,
                system_message="너는 최신 논문 트렌드를 분석하는 전문 연구 분석가이다."
            )
            # 결과 파싱 로직은 LLM 응답 형식에 따라 구현 필요
            # 여기서는 간단하게 전체 텍스트를 반환
            return {"trends_analysis": analysis_text}
        except Exception as e:
            logger.error(f"연구 동향 분석 실패: {e}", exc_info=True)
            return {"error": f"연구 동향 분석 실패: {e}", "trends": [], "keywords": []}
            
    def get_embedding_stats(self) -> Dict[str, Any]:
        """임베딩 통계 반환"""
        if self.paper_embeddings is None:
            return {"status": "No embeddings found"}
        return {
            "count": self.paper_embeddings.shape[0],
            "dimension": self.paper_embeddings.shape[1],
            "mean_norm": float(np.mean(np.linalg.norm(self.paper_embeddings, axis=1)))
        }

    async def discover_and_recommend(self, user_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """주어진 사용자 쿼리에 기반하여 논문 검색 및 추천 (고수준)"""
        try:
            if not self.paper_index:
                await self.build_paper_index([]) # 빈 데이터로 인덱스 초기화 시도
                if not self.paper_index:
                    logger.error("논문 인덱스를 초기화할 수 없습니다.")
                    return []

            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.encode([user_query])
            faiss.normalize_L2(query_embedding)

            # 유사 논문 검색
            similarities, indices = self.paper_index.search(
                query_embedding.astype('float32'),
                top_k * 2 # 더 많은 후보를 가져와서 필터링 가능성 열어둠
            )

            recommendations = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if idx == -1: # 유효하지 않은 인덱스
                    continue

                paper_id = list(self.paper_metadata.keys())[idx]
                paper = self.paper_metadata[paper_id]

                reason = await self._generate_recommendation_reason(
                    ResearchQuery(query_text=user_query, research_interests=[]), paper, similarity
                )

                recommendations.append({
                    'paper_id': paper_id,
                    'title': paper.get('title', ''),
                    'abstract': paper.get('abstract', ''),
                    'relevance_score': float(similarity),
                    'reason': reason
                })

                if len(recommendations) >= top_k:
                    break
            
            return recommendations

        except Exception as e:
            logger.error(f"discover_and_recommend 실패: {e}", exc_info=True)
            return [] 