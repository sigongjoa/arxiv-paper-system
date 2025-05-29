import requests
import logging
import json
from .config import LLM_API_URL

logger = logging.getLogger(__name__)

class LLMSummarizer:
    def __init__(self):
        self.base_url = LLM_API_URL
    
    def summarize_paper(self, paper):
        prompt = f"""다음 논문을 분석하여 정확한 JSON 형식으로 구조화된 요약을 작성하세요. 반드시 유효한 JSON만 출력하고 다른 텍스트는 포함하지 마세요.

{{
  "background": {{
    "problem_definition": "해결하고자 하는 구체적인 문제",
    "motivation": "연구의 구체적인 동기와 필요성"
  }},
  "contributions": ["주요 기여점 1", "주요 기여점 2", "주요 기여점 3"],
  "methodology": {{
    "approach": "사용된 구체적인 방법론과 접근법",
    "datasets": "사용된 데이터셋과 실험 설정"
  }},
  "results": {{
    "key_findings": "주요 발견사항과 결과",
    "performance": "성능 지표 및 개선사항"
  }}
}}

논문 정보:
제목: {paper['title']}
초록: {paper.get('abstract', 'No abstract available')[:800]}
카테고리: {paper.get('categories', 'Unknown')}

위 JSON 형식에 맞춰 한국어로 구체적인 내용을 채워서 응답하세요. JSON 외의 다른 텍스트는 절대 포함하지 마세요:"""
        
        payload = {
            "model": "llm",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        print(f"DEBUG: Sending LLM request for paper {paper.get('arxiv_id', 'unknown')}")
        print(f"DEBUG: LLM URL: {self.base_url}")
        print(f"DEBUG: Payload keys: {list(payload.keys())}")
        
        response = requests.post(self.base_url, json=payload, timeout=60)
        print(f"DEBUG: LLM response status: {response.status_code}")
        response.raise_for_status()
        
        response_data = response.json()
        print(f"DEBUG: LLM response keys: {list(response_data.keys())}")
        
        if 'choices' not in response_data or not response_data['choices']:
            raise Exception(f"ERROR: No choices in LLM response: {response_data}")
        
        summary_text = response_data['choices'][0]['message']['content'].strip()
        print(f"DEBUG: Raw LLM response length: {len(summary_text)}")
        print(f"DEBUG: Raw LLM response preview: {summary_text[:200]}...")
        
        # Remove markdown code blocks if present
        if summary_text.startswith('```'):
            summary_text = summary_text.split('```')[1]
            if summary_text.startswith('json'):
                summary_text = summary_text[4:]
        
        summary_text = summary_text.strip()
        
        # Validate JSON
        parsed = json.loads(summary_text)
        print(f"DEBUG: Successfully parsed JSON for {paper.get('arxiv_id', 'unknown')}")
        return summary_text

