import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from ..lm_studio import LMStudioClient

logger = logging.getLogger(__name__)

class CitationIntelligenceAgent:
    def __init__(self, lm_client: LMStudioClient = None):
        self.lm_client = lm_client or LMStudioClient()
        
    async def classify_citations(self, citing_paper: Dict, cited_papers: List[Dict]) -> Dict:
        """Classify citation relationships with smart analysis"""
        try:
            citation_analysis = {
                "citing_paper": citing_paper.get("arxiv_id"),
                "total_citations": len(cited_papers),
                "classifications": [],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            for cited_paper in cited_papers:
                classification = await self._classify_single_citation(citing_paper, cited_paper)
                citation_analysis["classifications"].append(classification)
            
            # Generate citation pattern summary
            summary = await self._generate_citation_summary(citation_analysis)
            citation_analysis["pattern_summary"] = summary
            
            logger.info(f"Citation classification completed for {citing_paper.get('arxiv_id')}")
            return citation_analysis
            
        except Exception as e:
            logger.error(f"Citation classification failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def _classify_single_citation(self, citing_paper: Dict, cited_paper: Dict) -> Dict:
        """Classify relationship between two papers"""
        try:
            prompt = f"""다음 두 논문의 인용 관계를 분석하여 JSON으로 분류하세요.

인용하는 논문:
제목: {citing_paper.get('title', '')}
초록: {citing_paper.get('abstract', '')[:800]}

인용되는 논문:
제목: {cited_paper.get('title', '')}
초록: {cited_paper.get('abstract', '')[:800]}

다음 JSON 형식으로 분류:
{{
  "cited_paper_id": "{cited_paper.get('arxiv_id', '')}",
  "relationship_type": "supporting/contradictory/methodological/background/comparison",
  "relevance_score": 85,
  "citation_context": {{
    "section": "introduction/methodology/results/discussion",
    "purpose": "인용 목적 설명",
    "sentiment": "positive/neutral/negative"
  }},
  "influence_level": {{
    "methodological_influence": 75,
    "theoretical_influence": 60,
    "empirical_influence": 80,
    "overall_influence": 72
  }},
  "relationship_description": "인용 관계에 대한 구체적 설명"
}}

JSON만 출력:"""

            response = await self.lm_client.generate_response(prompt, "technical_analysis")
            classification = json.loads(response)
            
            return classification
            
        except Exception as e:
            logger.error(f"Single citation classification failed: {e}")
            return {
                "cited_paper_id": cited_paper.get('arxiv_id', ''),
                "error": str(e)
            }
    
    async def _generate_citation_summary(self, citation_analysis: Dict) -> Dict:
        """Generate summary of citation patterns"""
        try:
            classifications = citation_analysis.get("classifications", [])
            
            if not classifications:
                return {"error": "No classifications to summarize"}
            
            # Calculate statistics
            relationship_types = [c.get("relationship_type", "unknown") for c in classifications]
            relevance_scores = [c.get("relevance_score", 0) for c in classifications if isinstance(c.get("relevance_score"), (int, float))]
            
            prompt = f"""다음 인용 분석 데이터를 요약하여 JSON으로 제공하세요.

분석된 인용 관계들:
{json.dumps(classifications[:10], indent=2, ensure_ascii=False)}

관계 유형 분포: {dict(zip(*np.unique(relationship_types, return_counts=True))) if relationship_types else {}}
평균 관련성 점수: {sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0:.1f}

다음 형식으로 요약:
{{
  "citation_patterns": {{
    "primary_citation_purpose": "주요 인용 목적",
    "dominant_relationship_type": "가장 많은 관계 유형",
    "citation_diversity": "인용 다양성 평가"
  }},
  "influence_analysis": {{
    "highly_influential_citations": ["high_influence_paper_1", "high_influence_paper_2"],
    "methodological_foundations": ["method_paper_1", "method_paper_2"],
    "theoretical_foundations": ["theory_paper_1", "theory_paper_2"]
  }},
  "citation_quality": {{
    "average_relevance": 85.5,
    "citation_depth": "superficial/moderate/deep",
    "coverage_assessment": "comprehensive/selective/narrow"
  }},
  "research_positioning": {{
    "builds_upon": ["foundational_work_1", "foundational_work_2"],
    "extends": ["extended_work_1", "extended_work_2"],
    "challenges": ["challenged_work_1", "challenged_work_2"]
  }}
}}

JSON만 출력:"""

            response = await self.lm_client.generate_response(prompt, "technical_analysis")
            summary = json.loads(response)
            
            return summary
            
        except Exception as e:
            logger.error(f"Citation summary generation failed: {e}")
            return {"error": str(e)}
    
    async def analyze_citation_network(self, paper_id: str, network_data: Dict) -> Dict:
        """Analyze citation network patterns"""
        try:
            nodes = network_data.get("nodes", [])
            edges = network_data.get("edges", [])
            
            prompt = f"""다음 인용 네트워크를 분석하여 JSON으로 제공하세요.

중심 논문: {paper_id}
노드 수: {len(nodes)}
엣지 수: {len(edges)}

네트워크 구조:
{json.dumps({"nodes": nodes[:20], "edges": edges[:20]}, indent=2, ensure_ascii=False)}

다음 형식으로 분석:
{{
  "network_metrics": {{
    "centrality_score": 85,
    "clustering_coefficient": 0.75,
    "network_density": 0.45,
    "influence_rank": "high/medium/low"
  }},
  "community_analysis": {{
    "research_clusters": [
      {{
        "cluster_name": "클러스터 1",
        "papers": ["paper_1", "paper_2"],
        "theme": "클러스터 주제"
      }}
    ],
    "interdisciplinary_connections": ["연결된 분야 1", "연결된 분야 2"]
  }},
  "temporal_patterns": {{
    "citation_trend": "increasing/stable/decreasing",
    "peak_citation_period": "최고 인용 시기",
    "recent_attention": "최근 관심도"
  }},
  "key_influencers": [
    {{
      "paper_id": "influential_paper_1",
      "influence_type": "methodological/theoretical/empirical",
      "influence_strength": 90
    }}
  ],
  "research_impact": {{
    "field_advancement": "분야 발전 기여도",
    "methodological_innovation": "방법론적 혁신 정도",
    "theoretical_contribution": "이론적 기여도"
  }}
}}

JSON만 출력:"""

            response = await self.lm_client.generate_response(prompt, "technical_analysis")
            analysis = json.loads(response)
            
            analysis["analyzed_at"] = datetime.now().isoformat()
            analysis["paper_id"] = paper_id
            
            return analysis
            
        except Exception as e:
            logger.error(f"Citation network analysis failed: {e}")
            return {"error": str(e), "paper_id": paper_id}
    
    async def recommend_citations(self, paper_data: Dict, candidate_papers: List[Dict]) -> Dict:
        """Recommend relevant citations for a paper"""
        try:
            prompt = f"""다음 논문에 대해 인용할 가치가 있는 후보 논문들을 평가하여 추천하세요.

대상 논문:
제목: {paper_data.get('title', '')}
초록: {paper_data.get('abstract', '')[:1000]}

후보 논문들:
{json.dumps([{"title": p.get("title", ""), "abstract": p.get("abstract", "")[:300], "arxiv_id": p.get("arxiv_id", "")} for p in candidate_papers[:10]], indent=2, ensure_ascii=False)}

다음 형식으로 추천:
{{
  "recommendations": [
    {{
      "paper_id": "paper_1",
      "recommendation_score": 92,
      "citation_rationale": "인용 추천 이유",
      "suggested_context": "인용할 섹션 및 맥락",
      "relationship_type": "supporting/methodological/comparison",
      "priority": "high/medium/low"
    }}
  ],
  "citation_strategy": {{
    "foundational_papers": ["기초 논문들"],
    "methodological_papers": ["방법론 논문들"], 
    "comparative_papers": ["비교 논문들"],
    "recent_advances": ["최신 연구들"]
  }},
  "coverage_assessment": {{
    "theoretical_coverage": "이론적 커버리지 평가",
    "methodological_coverage": "방법론적 커버리지 평가",
    "empirical_coverage": "실증적 커버리지 평가",
    "gaps_to_address": ["보완할 부분들"]
  }}
}}

JSON만 출력:"""

            response = await self.lm_client.generate_response(prompt, "technical_analysis")
            recommendations = json.loads(response)
            
            recommendations["generated_at"] = datetime.now().isoformat()
            recommendations["target_paper"] = paper_data.get("arxiv_id")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Citation recommendation failed: {e}")
            return {"error": str(e)}

# Helper function for numpy import in production
try:
    import numpy as np
except ImportError:
    # Fallback implementation without numpy
    def unique_with_counts(arr):
        counts = {}
        for item in arr:
            counts[item] = counts.get(item, 0) + 1
        return list(counts.keys()), list(counts.values())
    
    class np:
        @staticmethod
        def unique(arr, return_counts=False):
            if return_counts:
                return unique_with_counts(arr)
            else:
                return list(set(arr))
