import requests
import json
import logging

class LMStudioClient:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.base_url = base_url
        
    def extract_key_findings(self, paper_data):
        prompt = f"""논문에서 핵심 정보를 추출하여 JSON으로 응답하세요.

제목: {paper_data['title']}
초록: {paper_data['abstract']}

다음 JSON 형식으로만 응답:
{{
  "main_contribution": "주요 기여점",
  "methodology": "방법론 요약", 
  "results": "주요 결과",
  "impact": "예상 영향"
}}"""

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code != 200:
            logging.error(f"LM Studio API error: {response.status_code}")
            raise Exception(f"API error: {response.status_code}")
            
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # JSON 추출
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        return json.loads(content.strip())
        
    def generate_script(self, summary_data, paper_data):
        prompt = f"""논문을 60초 쇼츠 영상으로 만들 스크립트를 생성해주세요.

제목: {paper_data['title']}
요약: {summary_data}

다음 JSON 형식으로 정확히 응답해주세요:
{{
  "hook": "흥미로운 첫 문장 (5초)",
  "scenes": [
    {{"text": "첫 번째 장면 내레이션", "duration": 15, "visual": "title_card"}},
    {{"text": "두 번째 장면 내레이션", "duration": 20, "visual": "diagram"}},
    {{"text": "세 번째 장면 내레이션", "duration": 15, "visual": "chart"}},
    {{"text": "마무리 장면 내레이션", "duration": 5, "visual": "conclusion"}}
  ],
  "cta": "마무리 멘트"
}}

반드시 JSON 형식만 출력하고 다른 텍스트는 포함하지 마세요."""
            
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 800
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logging.error(f"LM Studio API error: {response.status_code}")
            raise Exception(f"API error: {response.status_code}")
            
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # JSON 추출
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        content = content.strip()
        return json.loads(content)
        
    def generate_shorts_script(self, summary_data, paper_data, hook):
        prompt = f"""양산형 YouTube 쇼츠용 60초 스크립트를 생성하세요.

제목: {paper_data['title']}
요약: {summary_data}
훅: {hook}

다음 JSON 형식으로 정확히 응답하세요:
{{
  "hook": "{hook}",
  "scenes": [
    {{"text": "첫 번째 장면 (3초)", "duration": 3, "visual": "hook_card"}},
    {{"text": "문제 설명 (12초)", "duration": 12, "visual": "problem_visual"}},
    {{"text": "해결 방법 (30초)", "duration": 30, "visual": "solution_chart"}},
    {{"text": "결과 및 영향 (15초)", "duration": 15, "visual": "impact_visual"}}
  ],
  "cta": "구독하고 더 많은 AI 연구를 확인하세요!"
}}

필수 조건:
- 총 60초 정확히 맞추기
- 첫 3초는 반드시 훅 사용
- 각 장면은 2-30초 사이
- 모바일 친화적 짧은 문장
- JSON 형식만 출력"""
            
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1000
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"ERROR: LM Studio API error {response.status_code}: {response.text}")
            
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # JSON 추출
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        content = content.strip()
        
        try:
            script_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"ERROR: Invalid JSON response from LM Studio: {e}")
            
        # 필수 필드 검증
        if not script_data.get('hook') or not script_data.get('scenes'):
            raise ValueError("ERROR: Generated script missing required fields (hook, scenes)")
            
        return script_data
