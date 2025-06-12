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
from backend.core.database import Paper  # Paper 모델 임포트
from backend.core.config import Config
from backend.core.llm_summarizer import LLMSummarizer as TextSummarizer # LLMSummarizer를 TextSummarizer로 임포트
from backend.core.recommendation_engine import ModernRecommendationEngine
from backend.core.arxiv_client import ArxivClient # Modified import path
from backend.core.paper_database import PaperDatabase
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

            try:
                logging.info("LM Studio Client를 통해 추천 이유 생성 요청.")
                reason = await self.llm_client.generate_response(prompt_messages, temperature=0.7, max_tokens=300)
                logging.info(f"LM Studio Client로부터 받은 추천 이유: {reason[:300]}...") # 받은 이유의 처음 300자 로깅
                return reason if reason else "추천 이유를 생성하지 못했습니다."
            except Exception as e:
                logging.error(f"추천 이유 생성 중 오류 발생: {e}")
                return "추천 이유 생성 중 오류가 발생했습니다."
            
        except Exception as e:
            logger.error(f"추천 이유 생성 실패: {e}", exc_info=True)
            return f"시맨틱 유사도 {similarity:.3f}로 추천된 논문입니다."

    async def generate_research_suggestions(self, papers: List[Dict[str, Any]]) -> List[str]:
        """연구 제안 생성"""
        try:
            logger.info(f"연구 제안 생성 시작: {len(papers)}개 논문 기반")
            
            # 논문 요약
            paper_summaries = []
            for paper in papers[:10]:  # 최대 10개 논문만 사용
                summary = f"- {paper.get('title', '')}: {paper.get('abstract', '')[:200]}"
                paper_summaries.append(summary)
            
            summaries_text = '\n'.join(paper_summaries)
            
            prompt = f"""다음 최근 논문들을 분석하여 새로운 연구 방향을 제안해주세요:

논문 목록:
{summaries_text}

제안 요구사항:
1. 연구 공백 및 기회 식별
2. 학제간 융합 연구 가능성
3. 실용적 응용 분야
4. 기술적 도전과제
5. JSON 형식으로 5-7개 제안: ["제안1", "제안2", ...]

연구 제안:"""
            
            response = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            try:
                suggestions = json.loads(response)
                if isinstance(suggestions, list):
                    return suggestions
            except:
                lines = response.split('\n')
                return [line.strip() for line in lines if line.strip() and not line.strip().startswith(('#', '-', '*'))]
            
            return []
            
        except Exception as e:
            logger.error(f"연구 제안 생성 실패: {e}", exc_info=True)
            return []

    async def analyze_research_trends(self, papers: List[Dict[str, Any]], time_window: str = "6months") -> Dict[str, Any]:
        """연구 트렌드 분석"""
        try:
            logger.info(f"연구 트렌드 분석 시작: {len(papers)}개 논문, 기간: {time_window}")
            
            # 키워드 빈도 분석
            all_keywords = []
            for paper in papers:
                keywords = paper.get('keywords', [])
                all_keywords.extend(keywords)
            
            # 상위 키워드 추출
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            top_keywords = keyword_counts.most_common(20)
            
            # 트렌드 분석을 위한 LLM 분석
            keywords_text = ', '.join([f"{kw}({count})" for kw, count in top_keywords])
            
            prompt = f"""다음 키워드 빈도를 바탕으로 최근 연구 트렌드를 분석해주세요:

주요 키워드: {keywords_text}
분석 기간: {time_window}
총 논문 수: {len(papers)}

분석 요구사항:
1. 급성장 분야 식별
2. 기술 융합 트렌드
3. 새로운 연구 방향
4. 한국어로 상세 분석

트렌드 분석:"""
            
            trend_analysis = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            return {
                'trend_summary': trend_analysis,
                'top_keywords': top_keywords,
                'total_papers': len(papers),
                'analysis_period': time_window,
                'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"연구 트렌드 분석 실패: {e}", exc_info=True)
            return {}

    def get_embedding_stats(self) -> Dict[str, Any]:
        """임베딩 통계 정보"""
        try:
            if not self.paper_index:
                return {'status': 'not_initialized'}
            
            return {
                'status': 'ready',
                'total_papers': self.paper_index.ntotal,
                'embedding_dimension': self.paper_index.d,
                'model_name': 'all-MiniLM-L6-v2'
            }
            
        except Exception as e:
            logger.error(f"임베딩 통계 조회 실패: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    async def discover_and_recommend(self, user_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # This method is not provided in the original file or the code block
        # It's assumed to exist as it's called in the code block
        pass
