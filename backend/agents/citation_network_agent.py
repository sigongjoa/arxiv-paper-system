"""Citation Network Agent for arXiv Research System"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
import time
import networkx as nx
from .lm_studio_client import LMStudioClient

logger = logging.getLogger(__name__)

@dataclass
class CitationRelation:
    """인용 관계"""
    citing_paper: str
    cited_paper: str
    citation_context: str
    citation_type: str  # 'direct', 'indirect', 'comparison', 'extension'
    confidence: float

@dataclass
class NetworkAnalysis:
    """네트워크 분석 결과"""
    influential_papers: List[Dict[str, Any]]
    research_clusters: List[Dict[str, Any]]
    citation_flow: Dict[str, List[str]]
    network_metrics: Dict[str, float]

class CitationNetworkAgent:
    """인용 네트워크 분석 AI 에이전트"""
    
    def __init__(self, llm_client: LMStudioClient):
        self.llm_client = llm_client
        self.citation_graph = nx.DiGraph()
        self.paper_metadata = {}
        self.system_prompt = """You are an expert citation analysis assistant.
Your task is to analyze citation patterns and research networks.
Always respond in Korean with detailed analysis."""

    async def extract_citations(self, paper_content: str, paper_id: str) -> List[CitationRelation]:
        """논문에서 인용 관계 추출"""
        try:
            logger.info(f"인용 관계 추출 시작: {paper_id}")
            start_time = time.time()
            
            # 기본 인용 패턴 매칭
            citation_patterns = [
                r'\[(\d+)\]',  # [1], [2] 형태
                r'\(([^)]+\s+\d{4})\)',  # (Author 2023) 형태
                r'([A-Z][a-z]+\s+et\s+al\.\s+\(\d{4}\))',  # Smith et al. (2023) 형태
            ]
            
            citations = []
            for pattern in citation_patterns:
                matches = re.finditer(pattern, paper_content)
                for match in matches:
                    citation_text = match.group(0)
                    context = self._extract_citation_context(paper_content, match.start(), match.end())
                    
                    # LLM을 사용한 인용 분석
                    citation_analysis = await self._analyze_citation(citation_text, context)
                    
                    if citation_analysis:
                        relation = CitationRelation(
                            citing_paper=paper_id,
                            cited_paper=citation_analysis.get('cited_paper', citation_text),
                            citation_context=context,
                            citation_type=citation_analysis.get('type', 'direct'),
                            confidence=citation_analysis.get('confidence', 0.7)
                        )
                        citations.append(relation)
            
            # 중복 제거
            unique_citations = self._deduplicate_citations(citations)
            
            extraction_time = time.time() - start_time
            logger.info(f"인용 관계 추출 완료 - 시간: {extraction_time:.2f}s, 인용 수: {len(unique_citations)}")
            
            return unique_citations
            
        except Exception as e:
            logger.error(f"인용 관계 추출 실패: {e}", exc_info=True)
            return []

    def _extract_citation_context(self, content: str, start: int, end: int, window: int = 200) -> str:
        """인용 컨텍스트 추출"""
        try:
            context_start = max(0, start - window)
            context_end = min(len(content), end + window)
            return content[context_start:context_end].strip()
        except Exception as e:
            logger.error(f"인용 컨텍스트 추출 실패: {e}", exc_info=True)
            return ""

    async def _analyze_citation(self, citation_text: str, context: str) -> Optional[Dict[str, Any]]:
        """인용 분석"""
        try:
            prompt = f"""다음 인용과 컨텍스트를 분석해주세요:

인용: {citation_text}
컨텍스트: {context}

분석 요구사항:
1. 인용 유형 (direct/indirect/comparison/extension/background)
2. 인용 목적 (method/result/theory/comparison)
3. 신뢰도 (0.0-1.0)
4. JSON 형식으로 반환

분석 결과:"""
            
            response = await self.llm_client.generate_response(
                prompt, self.system_prompt, max_tokens=300
            )
            
            try:
                analysis = json.loads(response)
                return analysis
            except:
                # JSON 파싱 실패 시 기본값 반환
                return {
                    'cited_paper': citation_text,
                    'type': 'direct',
                    'confidence': 0.6
                }
                
        except Exception as e:
            logger.error(f"인용 분석 실패: {e}", exc_info=True)
            return None

    def _deduplicate_citations(self, citations: List[CitationRelation]) -> List[CitationRelation]:
        """인용 중복 제거"""
        try:
            seen = set()
            unique_citations = []
            
            for citation in citations:
                key = (citation.citing_paper, citation.cited_paper)
                if key not in seen:
                    seen.add(key)
                    unique_citations.append(citation)
            
            return unique_citations
            
        except Exception as e:
            logger.error(f"인용 중복 제거 실패: {e}", exc_info=True)
            return citations

    async def build_citation_network(self, papers: List[Dict[str, Any]]) -> NetworkAnalysis:
        """인용 네트워크 구축"""
        try:
            logger.info(f"인용 네트워크 구축 시작: {len(papers)}개 논문")
            start_time = time.time()
            
            # 그래프 초기화
            self.citation_graph.clear()
            self.paper_metadata.clear()
            
            # 논문 메타데이터 저장
            for paper in papers:
                paper_id = paper['id']
                self.paper_metadata[paper_id] = paper
                self.citation_graph.add_node(paper_id, **paper)
            
            # 인용 관계 추출 및 추가
            all_citations = []
            for paper in papers:
                if 'content' in paper:
                    citations = await self.extract_citations(paper['content'], paper['id'])
                    all_citations.extend(citations)
                    
                    # 그래프에 엣지 추가
                    for citation in citations:
                        if citation.cited_paper in self.paper_metadata:
                            self.citation_graph.add_edge(
                                citation.citing_paper,
                                citation.cited_paper,
                                type=citation.citation_type,
                                confidence=citation.confidence,
                                context=citation.citation_context
                            )
            
            # 네트워크 분석 수행
            analysis = await self._analyze_network()
            
            build_time = time.time() - start_time
            logger.info(f"인용 네트워크 구축 완료 - 시간: {build_time:.2f}s")
            
            return analysis
            
        except Exception as e:
            logger.error(f"인용 네트워크 구축 실패: {e}", exc_info=True)
            return NetworkAnalysis([], [], {}, {})

    async def _analyze_network(self) -> NetworkAnalysis:
        """네트워크 분석 수행"""
        try:
            logger.info("네트워크 분석 시작")
            
            # 영향력 있는 논문 식별
            influential_papers = self._identify_influential_papers()
            
            # 연구 클러스터 탐지
            clusters = self._detect_research_clusters()
            
            # 인용 흐름 분석
            citation_flow = self._analyze_citation_flow()
            
            # 네트워크 메트릭 계산
            metrics = self._calculate_network_metrics()
            
            return NetworkAnalysis(
                influential_papers=influential_papers,
                research_clusters=clusters,
                citation_flow=citation_flow,
                network_metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"네트워크 분석 실패: {e}", exc_info=True)
            return NetworkAnalysis([], [], {}, {})

    def _identify_influential_papers(self) -> List[Dict[str, Any]]:
        """영향력 있는 논문 식별"""
        try:
            if not self.citation_graph.nodes():
                return []
            
            # 다양한 중심성 지표 계산
            try:
                pagerank = nx.pagerank(self.citation_graph)
                in_degree = dict(self.citation_graph.in_degree())
                betweenness = nx.betweenness_centrality(self.citation_graph)
            except:
                # 그래프가 연결되지 않은 경우 기본값 사용
                pagerank = {node: 0.0 for node in self.citation_graph.nodes()}
                in_degree = {node: 0 for node in self.citation_graph.nodes()}
                betweenness = {node: 0.0 for node in self.citation_graph.nodes()}
            
            # 종합 영향력 점수 계산
            papers = []
            for paper_id in self.citation_graph.nodes():
                if paper_id in self.paper_metadata:
                    paper = self.paper_metadata[paper_id].copy()
                    paper['influence_metrics'] = {
                        'pagerank': pagerank.get(paper_id, 0.0),
                        'citation_count': in_degree.get(paper_id, 0),
                        'betweenness': betweenness.get(paper_id, 0.0),
                        'combined_score': (
                            pagerank.get(paper_id, 0.0) * 0.4 +
                            (in_degree.get(paper_id, 0) / max(in_degree.values()) if in_degree.values() else 0) * 0.4 +
                            betweenness.get(paper_id, 0.0) * 0.2
                        )
                    }
                    papers.append(paper)
            
            # 영향력 순으로 정렬
            papers.sort(key=lambda x: x['influence_metrics']['combined_score'], reverse=True)
            
            return papers[:20]  # 상위 20개 반환
            
        except Exception as e:
            logger.error(f"영향력 있는 논문 식별 실패: {e}", exc_info=True)
            return []

    def _detect_research_clusters(self) -> List[Dict[str, Any]]:
        """연구 클러스터 탐지"""
        try:
            if not self.citation_graph.nodes():
                return []
            
            # 커뮤니티 탐지 (undirected 그래프로 변환)
            undirected_graph = self.citation_graph.to_undirected()
            
            try:
                communities = nx.community.greedy_modularity_communities(undirected_graph)
            except:
                # 커뮤니티 탐지 실패 시 단일 클러스터로 처리
                communities = [set(self.citation_graph.nodes())]
            
            clusters = []
            for i, community in enumerate(communities):
                if len(community) >= 3:  # 최소 3개 논문으로 구성된 클러스터만
                    cluster_papers = [self.paper_metadata[paper_id] for paper_id in community 
                                    if paper_id in self.paper_metadata]
                    
                    cluster = {
                        'cluster_id': i,
                        'paper_count': len(cluster_papers),
                        'papers': cluster_papers[:10],  # 최대 10개만 포함
                        'keywords': self._extract_cluster_keywords(cluster_papers)
                    }
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"연구 클러스터 탐지 실패: {e}", exc_info=True)
            return []

    def _extract_cluster_keywords(self, papers: List[Dict[str, Any]]) -> List[str]:
        """클러스터 키워드 추출"""
        try:
            all_keywords = []
            for paper in papers:
                keywords = paper.get('keywords', [])
                all_keywords.extend(keywords)
            
            # 빈도수 기반 상위 키워드 추출
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            return [kw for kw, count in keyword_counts.most_common(10)]
            
        except Exception as e:
            logger.error(f"클러스터 키워드 추출 실패: {e}", exc_info=True)
            return []

    def _analyze_citation_flow(self) -> Dict[str, List[str]]:
        """인용 흐름 분석"""
        try:
            citation_flow = {}
            
            for node in self.citation_graph.nodes():
                # 인용하는 논문들 (outgoing)
                citing = list(self.citation_graph.successors(node))
                # 인용받는 논문들 (incoming)
                cited_by = list(self.citation_graph.predecessors(node))
                
                citation_flow[node] = {
                    'cites': citing,
                    'cited_by': cited_by,
                    'citation_ratio': len(citing) / max(len(cited_by), 1)
                }
            
            return citation_flow
            
        except Exception as e:
            logger.error(f"인용 흐름 분석 실패: {e}", exc_info=True)
            return {}

    def _calculate_network_metrics(self) -> Dict[str, float]:
        """네트워크 메트릭 계산"""
        try:
            if not self.citation_graph.nodes():
                return {}
            
            metrics = {
                'total_nodes': self.citation_graph.number_of_nodes(),
                'total_edges': self.citation_graph.number_of_edges(),
                'density': nx.density(self.citation_graph),
                'average_clustering': 0.0,
                'average_path_length': 0.0
            }
            
            # 연결된 컴포넌트가 있는 경우에만 계산
            if self.citation_graph.number_of_edges() > 0:
                try:
                    undirected = self.citation_graph.to_undirected()
                    metrics['average_clustering'] = nx.average_clustering(undirected)
                    
                    # 가장 큰 연결 컴포넌트에서 평균 경로 길이 계산
                    largest_cc = max(nx.connected_components(undirected), key=len)
                    subgraph = undirected.subgraph(largest_cc)
                    if len(subgraph) > 1:
                        metrics['average_path_length'] = nx.average_shortest_path_length(subgraph)
                except:
                    pass  # 계산 실패 시 기본값 유지
            
            return metrics
            
        except Exception as e:
            logger.error(f"네트워크 메트릭 계산 실패: {e}", exc_info=True)
            return {}

    async def generate_citation_insights(self, paper_id: str) -> Dict[str, Any]:
        """특정 논문의 인용 인사이트 생성"""
        try:
            logger.info(f"인용 인사이트 생성: {paper_id}")
            
            if paper_id not in self.citation_graph:
                return {'error': '논문을 찾을 수 없음'}
            
            paper = self.paper_metadata.get(paper_id, {})
            
            # 인용 통계
            citing_papers = list(self.citation_graph.predecessors(paper_id))
            cited_papers = list(self.citation_graph.successors(paper_id))
            
            # LLM을 사용한 인사이트 생성
            prompt = f"""다음 논문의 인용 패턴을 분석하고 인사이트를 제공해주세요:

논문: {paper.get('title', '')}
인용받은 횟수: {len(citing_papers)}
인용한 논문 수: {len(cited_papers)}

분석 요구사항:
1. 인용 패턴의 특징
2. 연구 영향력 평가
3. 학술적 위치 분석
4. 한국어로 상세 분석

인용 인사이트:"""
            
            insight_text = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            return {
                'paper_id': paper_id,
                'citation_stats': {
                    'cited_by_count': len(citing_papers),
                    'cites_count': len(cited_papers),
                    'citation_ratio': len(citing_papers) / max(len(cited_papers), 1)
                },
                'citing_papers': citing_papers[:10],
                'cited_papers': cited_papers[:10],
                'insights': insight_text,
                'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"인용 인사이트 생성 실패: {e}", exc_info=True)
            return {'error': str(e)}

    def get_network_stats(self) -> Dict[str, Any]:
        """네트워크 통계 정보"""
        try:
            return {
                'status': 'ready' if self.citation_graph.nodes() else 'empty',
                'total_papers': len(self.paper_metadata),
                'total_citations': self.citation_graph.number_of_edges(),
                'network_density': nx.density(self.citation_graph) if self.citation_graph.nodes() else 0.0
            }
            
        except Exception as e:
            logger.error(f"네트워크 통계 조회 실패: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
