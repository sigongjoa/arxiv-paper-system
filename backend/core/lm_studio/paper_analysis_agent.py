import logging
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from .client import LMStudioClient

logger = logging.getLogger(__name__)

class PaperAnalysisAgent:
    def __init__(self, lm_client: LMStudioClient = None):
        self.lm_client = lm_client or LMStudioClient()
        self.analysis_templates = AcademicPromptTemplates()
    
    async def analyze_paper_comprehensive(self, paper_data: Dict) -> Dict:
        """Comprehensive paper analysis with structured output"""
        try:
            prompt = self.analysis_templates.comprehensive_analysis_prompt(paper_data)
            
            use_case = self.lm_client.get_optimal_model(
                "comprehensive_analysis", 
                len(paper_data.get('abstract', ''))
            )
            
            response = await self.lm_client.generate_response(prompt, use_case)
            
            analysis_result = json.loads(response)
            
            # Add metadata
            analysis_result.update({
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": self.lm_client.models[use_case]["name"],
                "arxiv_id": paper_data.get("arxiv_id")
            })
            
            logger.info(f"Comprehensive analysis completed for {paper_data.get('arxiv_id')}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def extract_methodology_details(self, paper_data: Dict) -> Dict:
        """Extract detailed methodology information"""
        try:
            prompt = self.analysis_templates.methodology_extraction_prompt(paper_data)
            
            response = await self.lm_client.generate_response(
                prompt, 
                "technical_analysis"
            )
            
            methodology_result = json.loads(response)
            methodology_result["extracted_at"] = datetime.now().isoformat()
            
            return methodology_result
            
        except Exception as e:
            logger.error(f"Methodology extraction failed: {e}")
            return {"error": str(e)}
    
    async def assess_reproducibility(self, paper_data: Dict) -> Dict:
        """Assess paper reproducibility"""
        try:
            prompt = self.analysis_templates.reproducibility_assessment_prompt(paper_data)
            
            response = await self.lm_client.generate_response(
                prompt,
                "technical_analysis"
            )
            
            reproducibility_result = json.loads(response)
            reproducibility_result["assessed_at"] = datetime.now().isoformat()
            
            return reproducibility_result
            
        except Exception as e:
            logger.error(f"Reproducibility assessment failed: {e}")
            return {"error": str(e)}
    
    async def identify_research_gaps(self, paper_data: Dict, related_papers: List[Dict] = None) -> Dict:
        """Identify research gaps and opportunities"""
        try:
            prompt = self.analysis_templates.research_gaps_prompt(paper_data, related_papers)
            
            response = await self.lm_client.generate_response(
                prompt,
                "technical_analysis"
            )
            
            gaps_result = json.loads(response)
            gaps_result["identified_at"] = datetime.now().isoformat()
            
            return gaps_result
            
        except Exception as e:
            logger.error(f"Research gaps identification failed: {e}")
            return {"error": str(e)}

class AcademicPromptTemplates:
    """Academic analysis prompt templates"""
    
    def comprehensive_analysis_prompt(self, paper_data: Dict) -> str:
        return f"""다음 논문을 종합적으로 분석하여 구조화된 JSON으로 제공하세요.

논문 정보:
제목: {paper_data.get('title', '')}
초록: {paper_data.get('abstract', '')[:2000]}
카테고리: {paper_data.get('categories', [])}
저자: {paper_data.get('authors', [])}

다음 JSON 구조로 분석하세요:
{{
  "background": {{
    "problem_definition": "해결하고자 하는 문제의 명확한 정의",
    "motivation": "연구 동기와 필요성",
    "related_work_summary": "관련 연구 요약"
  }},
  "methodology": {{
    "approach": "사용된 방법론의 구체적 설명",
    "novelty_aspects": ["새로운 점 1", "새로운 점 2"],
    "technical_contributions": ["기술적 기여 1", "기술적 기여 2"],
    "implementation_details": "구현 세부사항"
  }},
  "results_and_evaluation": {{
    "key_findings": ["주요 발견사항 1", "주요 발견사항 2"],
    "performance_metrics": "성능 지표 및 개선사항",
    "experimental_setup": "실험 설정 및 데이터셋",
    "limitations": ["한계점 1", "한계점 2"]
  }},
  "impact_assessment": {{
    "theoretical_significance": "이론적 중요성 (1-10점)",
    "practical_applications": ["실용적 응용 1", "실용적 응용 2"],
    "field_advancement": "해당 분야 발전에 미치는 영향",
    "citation_potential": "인용 가능성 예측 (1-10점)"
  }},
  "quality_scores": {{
    "methodology_rigor": 85,
    "novelty": 78,
    "clarity": 82,
    "reproducibility": 75,
    "significance": 80,
    "overall": 80
  }},
  "future_directions": [
    "향후 연구 방향 1",
    "향후 연구 방향 2",
    "향후 연구 방향 3"
  ],
  "recommendations": {{
    "for_researchers": ["연구자를 위한 권장사항 1", "연구자를 위한 권장사항 2"],
    "for_practitioners": ["실무자를 위한 권장사항 1", "실무자를 위한 권장사항 2"]
  }}
}}

JSON만 출력하세요:"""

    def methodology_extraction_prompt(self, paper_data: Dict) -> str:
        return f"""다음 논문의 방법론을 자세히 분석하여 JSON으로 제공하세요.

논문: {paper_data.get('title', '')}
초록: {paper_data.get('abstract', '')[:1500]}

다음 형식으로 출력:
{{
  "methodology_type": "사용된 방법론 유형 (예: 실험적, 이론적, 시뮬레이션)",
  "core_algorithms": ["핵심 알고리즘 1", "핵심 알고리즘 2"],
  "data_requirements": {{
    "dataset_type": "필요한 데이터셋 유형",
    "data_size": "데이터 크기 요구사항",
    "preprocessing": "전처리 요구사항"
  }},
  "computational_complexity": {{
    "time_complexity": "시간 복잡도",
    "space_complexity": "공간 복잡도",
    "hardware_requirements": "하드웨어 요구사항"
  }},
  "experimental_design": {{
    "evaluation_metrics": ["평가 지표 1", "평가 지표 2"],
    "baseline_comparisons": ["비교 기준 1", "비교 기준 2"],
    "statistical_methods": "사용된 통계적 방법"
  }},
  "reproducibility_factors": {{
    "code_availability": "코드 공개 여부",
    "implementation_details": "구현 세부사항 제공 정도",
    "parameter_settings": "매개변수 설정 명시 정도"
  }}
}}

JSON만 출력:"""

    def reproducibility_assessment_prompt(self, paper_data: Dict) -> str:
        return f"""다음 논문의 재현가능성을 평가하여 JSON으로 제공하세요.

논문: {paper_data.get('title', '')}
초록: {paper_data.get('abstract', '')[:1500]}

다음 형식으로 평가:
{{
  "reproducibility_score": {{
    "code_availability": 8,
    "data_availability": 7,
    "method_clarity": 9,
    "parameter_specification": 8,
    "environment_description": 6,
    "overall_score": 76
  }},
  "reproducibility_checklist": {{
    "source_code_provided": true,
    "datasets_accessible": false,
    "hyperparameters_specified": true,
    "computational_environment_described": true,
    "random_seeds_specified": false,
    "statistical_significance_tested": true
  }},
  "missing_elements": [
    "누락된 재현 요소 1",
    "누락된 재현 요소 2"
  ],
  "recommendations_for_improvement": [
    "재현성 개선 권장사항 1",
    "재현성 개선 권장사항 2"
  ],
  "estimated_reproduction_difficulty": "쉬움/보통/어려움",
  "required_expertise_level": "초급/중급/고급"
}}

JSON만 출력:"""

    def research_gaps_prompt(self, paper_data: Dict, related_papers: List[Dict] = None) -> str:
        related_context = ""
        if related_papers:
            related_context = f"\n관련 논문들:\n" + "\n".join([
                f"- {p.get('title', '')}: {p.get('abstract', '')[:200]}..."
                for p in related_papers[:3]
            ])

        return f"""다음 논문과 관련 연구를 분석하여 연구 공백과 기회를 식별하세요.

논문: {paper_data.get('title', '')}
초록: {paper_data.get('abstract', '')[:1500]}
{related_context}

다음 형식으로 출력:
{{
  "identified_gaps": {{
    "methodological_gaps": [
      "방법론적 공백 1",
      "방법론적 공백 2"
    ],
    "empirical_gaps": [
      "실증적 공백 1",
      "실증적 공백 2"
    ],
    "theoretical_gaps": [
      "이론적 공백 1",
      "이론적 공백 2"
    ],
    "application_gaps": [
      "응용 분야 공백 1",
      "응용 분야 공백 2"
    ]
  }},
  "research_opportunities": {{
    "short_term": [
      "단기 연구 기회 1",
      "단기 연구 기회 2"
    ],
    "long_term": [
      "장기 연구 기회 1",
      "장기 연구 기회 2"
    ],
    "interdisciplinary": [
      "학제간 연구 기회 1",
      "학제간 연구 기회 2"
    ]
  }},
  "impact_potential": {{
    "academic_impact": "학술적 영향 예상",
    "industry_impact": "산업적 영향 예상",
    "societal_impact": "사회적 영향 예상"
  }},
  "recommended_next_steps": [
    "권장되는 다음 단계 1",
    "권장되는 다음 단계 2",
    "권장되는 다음 단계 3"
  ]
}}

JSON만 출력:"""
