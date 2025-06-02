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
