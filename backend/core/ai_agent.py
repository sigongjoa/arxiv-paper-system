import requests
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.config import LLM_API_URL
from core.database import DatabaseManager

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.base_url = LLM_API_URL
        self.db = DatabaseManager()
        self.conversation_history = {}
        
    async def analyze_paper_comprehensive(self, paper_data: Dict) -> Dict:
        """종합적인 논문 분석"""
        try:
            prompt = f"""다음 논문을 종합적으로 분석하여 JSON 형식으로 구조화된 분석을 제공하세요.

논문 정보:
제목: {paper_data['title']}
초록: {paper_data.get('abstract', '')[:1000]}
카테고리: {paper_data.get('categories', [])}
저자: {paper_data.get('authors', [])}

다음 JSON 형식으로 분석하세요:
{{
  "executive_summary": "논문의 핵심 내용을 3-4문장으로 요약",
  "problem_statement": "해결하고자 하는 문제의 명확한 정의",
  "methodology": {{
    "approach": "사용된 방법론의 구체적 설명",
    "novelty": "기존 연구 대비 새로운 점",
    "technical_details": "주요 기술적 세부사항"
  }},
  "contributions": [
    "주요 기여점 1",
    "주요 기여점 2", 
    "주요 기여점 3"
  ],
  "strengths": [
    "논문의 강점 1",
    "논문의 강점 2"
  ],
  "limitations": [
    "한계점 1",
    "한계점 2"
  ],
  "impact_assessment": {{
    "theoretical_significance": "이론적 중요성 평가",
    "practical_applications": "실용적 응용 가능성",
    "field_advancement": "해당 분야에 미치는 영향"
  }},
  "quality_score": {{
    "methodology_rigor": 85,
    "novelty": 78,
    "clarity": 82,
    "reproducibility": 75,
    "overall": 80
  }},
  "research_directions": [
    "향후 연구 방향 1",
    "향후 연구 방향 2"
  ]
}}

유효한 JSON만 출력하세요:"""

            response = await self._call_llm(prompt, max_tokens=1500)
            return json.loads(response.strip())
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {"error": str(e)}
    
    async def extract_key_findings(self, paper_data: Dict) -> Dict:
        """핵심 발견사항 추출"""
        try:
            prompt = f"""논문에서 핵심 발견사항을 추출하여 JSON으로 구조화하세요.

논문: {paper_data['title']}
초록: {paper_data.get('abstract', '')[:800]}

다음 형식으로 출력하세요:
{{
  "main_findings": [
    "핵심 발견사항 1",
    "핵심 발견사항 2"
  ],
  "key_metrics": {{
    "performance_improvements": "성능 개선 수치",
    "comparison_results": "비교 실험 결과"
  }},
  "novel_insights": [
    "새로운 통찰 1",
    "새로운 통찰 2"
  ],
  "validation_methods": [
    "검증 방법 1",
    "검증 방법 2"
  ]
}}

JSON만 출력:"""

            response = await self._call_llm(prompt, max_tokens=800)
            return json.loads(response.strip())
            
        except Exception as e:
            logger.error(f"Key findings extraction failed: {e}")
            return {"error": str(e)}
    
    async def assess_paper_quality(self, paper_data: Dict) -> Dict:
        """논문 품질 평가"""
        try:
            prompt = f"""다음 논문의 품질을 다각도로 평가하여 JSON으로 제공하세요.

논문: {paper_data['title']}
초록: {paper_data.get('abstract', '')[:800]}
카테고리: {paper_data.get('categories', [])}

평가 기준:
1. 방법론의 엄밀성 (0-100)
2. 참신성/독창성 (0-100)  
3. 명확성/가독성 (0-100)
4. 재현가능성 (0-100)
5. 실용적 가치 (0-100)

다음 형식으로 출력:
{{
  "quality_assessment": {{
    "methodology_rigor": 85,
    "novelty": 78,
    "clarity": 82, 
    "reproducibility": 75,
    "practical_value": 80,
    "overall_score": 80
  }},
  "detailed_feedback": {{
    "strengths": [
      "강점 1",
      "강점 2"
    ],
    "weaknesses": [
      "약점 1", 
      "약점 2"
    ],
    "improvement_suggestions": [
      "개선 제안 1",
      "개선 제안 2"
    ]
  }},
  "peer_review_readiness": {{
    "ready_for_submission": true,
    "required_improvements": [
      "필요한 개선사항"
    ]
  }}
}}

JSON만 출력:"""

            response = await self._call_llm(prompt, max_tokens=1000)
            return json.loads(response.strip())
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {"error": str(e)}
    
    async def chat_with_paper(self, paper_id: str, user_message: str, session_id: str) -> Dict:
        """논문과 대화형 상호작용"""
        try:
            # 논문 정보 조회
            paper = self.db.get_paper_by_id(paper_id)
            if not paper:
                return {"error": "논문을 찾을 수 없습니다."}
            
            paper_data = {
                'title': paper.title,
                'abstract': paper.abstract,
                'categories': paper.categories,
                'authors': paper.authors
            }
            
            # 대화 히스토리 관리
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            history = self.conversation_history[session_id]
            
            # 컨텍스트 구성
            context_prompt = f"""다음 논문에 대한 질문에 답변하세요:

논문 제목: {paper_data['title']}
저자: {', '.join(paper_data['authors'][:3])}
카테고리: {', '.join(paper_data['categories'])}
초록: {paper_data['abstract'][:1000]}

이전 대화:"""
            
            for msg in history[-3:]:  # 최근 3개 대화만 포함
                context_prompt += f"\n사용자: {msg['user']}\n답변: {msg['assistant']}"
            
            context_prompt += f"\n\n현재 질문: {user_message}\n\n답변 형식:\n{{\n  \"answer\": \"구체적이고 도움이 되는 답변\",\n  \"confidence\": 90,\n  \"sources\": [\"논문의 해당 섹션 또는 근거\"]\n}}\n\nJSON만 출력:"
            
            response = await self._call_llm(context_prompt, max_tokens=600)
            result = json.loads(response.strip())
            
            # 대화 히스토리 업데이트
            history.append({
                "user": user_message,
                "assistant": result.get("answer", ""),
                "timestamp": datetime.now().isoformat()
            })
            
            # 히스토리 크기 제한
            if len(history) > 10:
                history.pop(0)
            
            result["paper_id"] = paper_id
            result["session_id"] = session_id
            
            return result
            
        except Exception as e:
            logger.error(f"Chat interaction failed: {e}")
            return {"error": str(e)}
    
    async def suggest_related_papers(self, paper_id: str, limit: int = 5) -> Dict:
        """관련 논문 추천"""
        try:
            # 현재 논문 정보 조회
            paper = self.db.get_paper_by_id(paper_id)
            if not paper:
                return {"error": "논문을 찾을 수 없습니다."}
            
            # 같은 카테고리의 최근 논문들 조회 - search_papers 사용
            # 카테고리 문자열로 검색
            category_query = ' '.join(paper.categories) if isinstance(paper.categories, list) else str(paper.categories)
            all_papers = self.db.search_papers(category_query, limit=limit*3)
            
            # 현재 논문 제외
            related_papers = [p for p in all_papers if p.paper_id != paper_id]
            
            if not related_papers:
                return {"related_papers": [], "message": "관련 논문을 찾을 수 없습니다."}
            
            # LLM을 사용한 관련성 평가
            papers_text = ""
            for i, rp in enumerate(related_papers[:10]):  # 최대 10개만 평가
                papers_text += f"{i+1}. {rp.title}\n초록: {rp.abstract[:200]}...\n\n"
            
            prompt = f"""기준 논문과 가장 관련성이 높은 논문 {limit}개를 선별하여 JSON으로 제공하세요.

기준 논문:
제목: {paper.title}
초록: {paper.abstract[:400]}

후보 논문들:
{papers_text}

다음 형식으로 관련성이 높은 순으로 {limit}개 선별:
{{
  "related_papers": [
    {{
      "rank": 1,
      "paper_number": 3,
      "relevance_score": 92,
      "relationship_type": "방법론적 유사성",
      "reason": "왜 관련성이 높은지 설명"
    }}
  ]
}}

JSON만 출력:"""

            response = await self._call_llm(prompt, max_tokens=800)
            result = json.loads(response.strip())
            
            # 선별된 논문들의 상세 정보 추가
            selected_papers = []
            for selection in result.get("related_papers", []):
                paper_idx = selection["paper_number"] - 1
                if 0 <= paper_idx < len(related_papers):
                    rp = related_papers[paper_idx]
                    selected_papers.append({
                        "arxiv_id": rp.paper_id,
                        "title": rp.title,
                        "authors": rp.authors.split(',')[:3] if rp.authors else [],
                        "categories": rp.categories.split(',') if rp.categories else [],
                        "published_date": rp.published_date.isoformat() if rp.published_date else '',
                        "relevance_score": selection["relevance_score"],
                        "relationship_type": selection["relationship_type"],
                        "reason": selection["reason"]
                    })
            
            return {
                "source_paper": {
                    "arxiv_id": paper.paper_id,
                    "title": paper.title
                },
                "related_papers": selected_papers,
                "total_found": len(selected_papers)
            }
            
        except Exception as e:
            logger.error(f"Related papers suggestion failed: {e}")
            return {"error": str(e)}
    
    async def generate_research_questions(self, paper_data: Dict) -> Dict:
        """연구 질문 생성"""
        try:
            prompt = f"""다음 논문을 바탕으로 후속 연구를 위한 구체적인 연구 질문들을 생성하세요.

논문: {paper_data['title']}
초록: {paper_data.get('abstract', '')[:800]}
카테고리: {paper_data.get('categories', [])}

다음 형식으로 출력:
{{
  "follow_up_questions": [
    "이 연구를 확장할 수 있는 구체적 질문 1",
    "이 연구를 확장할 수 있는 구체적 질문 2"
  ],
  "methodological_questions": [
    "방법론 개선 관련 질문 1",
    "방법론 개선 관련 질문 2"
  ],
  "application_questions": [
    "실용적 응용 관련 질문 1",
    "실용적 응용 관련 질문 2"
  ],
  "theoretical_questions": [
    "이론적 발전 관련 질문 1",
    "이론적 발전 관련 질문 2"
  ]
}}

JSON만 출력:"""

            response = await self._call_llm(prompt, max_tokens=800)
            return json.loads(response.strip())
            
        except Exception as e:
            logger.error(f"Research questions generation failed: {e}")
            return {"error": str(e)}
    
    async def compare_papers(self, paper_ids: List[str]) -> Dict:
        """논문 비교 분석"""
        try:
            if len(paper_ids) < 2:
                return {"error": "비교를 위해 최소 2개의 논문이 필요합니다."}
            
            papers = []
            for paper_id in paper_ids[:3]:  # 최대 3개까지 비교
                paper = self.db.get_paper_by_id(paper_id)
                if paper:
                    papers.append({
                        "id": paper.paper_id,
                        "title": paper.title,
                        "abstract": paper.abstract[:500],
                        "categories": paper.categories.split(',') if paper.categories else []
                    })
            
            if len(papers) < 2:
                return {"error": "유효한 논문이 충분하지 않습니다."}
            
            papers_text = ""
            for i, p in enumerate(papers):
                papers_text += f"논문 {i+1}: {p['title']}\n초록: {p['abstract']}\n카테고리: {', '.join(p['categories'])}\n\n"
            
            prompt = f"""다음 논문들을 비교 분석하여 JSON으로 제공하세요:

{papers_text}

다음 형식으로 출력:
{{
  "comparison_matrix": {{
    "methodology": {{
      "논문1": "방법론 설명",
      "논문2": "방법론 설명"
    }},
    "contributions": {{
      "논문1": ["기여점1", "기여점2"],
      "논문2": ["기여점1", "기여점2"]
    }}
  }},
  "similarities": [
    "공통점 1",
    "공통점 2"
  ],
  "differences": [
    "차이점 1",
    "차이점 2"
  ],
  "complementarity": "논문들이 어떻게 상호 보완적인지",
  "research_gaps": [
    "발견된 연구 공백 1",
    "발견된 연구 공백 2"
  ]
}}

JSON만 출력:"""

            response = await self._call_llm(prompt, max_tokens=1200)
            result = json.loads(response.strip())
            result["compared_papers"] = [{"id": p["id"], "title": p["title"]} for p in papers]
            
            return result
            
        except Exception as e:
            logger.error(f"Paper comparison failed: {e}")
            return {"error": str(e)}
    
    async def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """LM Studio API 호출"""
        try:
            payload = {
                "model": "llm",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.base_url, json=payload, timeout=120)
            response.raise_for_status()
            
            response_data = response.json()
            if 'choices' not in response_data or not response_data['choices']:
                raise Exception("Invalid LLM response format")
            
            content = response_data['choices'][0]['message']['content'].strip()
            
            # 마크다운 코드 블록 제거
            if content.startswith('```'):
                lines = content.split('\n')
                if lines[0].strip() == '```json' or lines[0].strip() == '```':
                    content = '\n'.join(lines[1:])
                if content.endswith('```'):
                    content = content[:-3]
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise e
    
    def clear_conversation_history(self, session_id: str):
        """대화 히스토리 초기화"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
