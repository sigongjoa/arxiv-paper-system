import requests
import logging

class ShortScriptGenerator:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.base_url = base_url

    def generate_short_script(self, paper_content, figure_analysis, audience_level="general"):
        logging.info(f"Generating short script with LM Studio for audience: {audience_level}")
        
        if not self.base_url:
            raise Exception("LM Studio base_url not configured")
            
        return self._generate_with_lm_studio(paper_content, figure_analysis, audience_level)

    def _generate_with_lm_studio(self, paper_content, figure_analysis, audience_level):
        prompt = f"""논문 제목: {paper_content.get('title', 'Unknown')}
초록: {paper_content.get('abstract', 'No abstract')[:200]}...
그림 분석: {figure_analysis}
청중 레벨: {audience_level}

60초 쇼츠 스크립트를 다음 구조로 생성하세요:
- 후크 (0-5초): 주의 끌기
- 맥락 (5-10초): 배경 설명
- 설명 (10-50초): 핵심 내용
- 적용 (50-57초): 실생활 연결
- CTA (57-60초): 행동 유도

{audience_level}용 언어로 작성하세요."""
        
        logging.info(f"Sending prompt to LM Studio: {prompt[:100]}...")
        
        payload = {
            "model": "local-model",
            "messages": [
                {"role": "system", "content": "당신은 60초 쇼츠 스크립트 제작 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 600
        }
        
        logging.info(f"Calling LM Studio API at: {self.base_url}/v1/chat/completions")
        
        try:
            response = requests.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=30)
            
            logging.info(f"LM Studio API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                script_text = result['choices'][0]['message']['content']
                logging.info(f"LM Studio response received: {script_text[:200]}...")
                return self._structure_script(script_text)
            else:
                logging.error(f"LM Studio API error: {response.status_code} - {response.text}")
                raise Exception(f"LM Studio API error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"LM Studio connection error: {e}")
            raise Exception(f"LM Studio connection error: {e}")

    def _structure_script(self, script_text):
        return {
            "hook": {"content": self._extract_section(script_text, "후크"), "duration": 5},
            "context": {"content": self._extract_section(script_text, "맥락"), "duration": 5},
            "explanation": {"content": self._extract_section(script_text, "설명"), "duration": 40},
            "application": {"content": self._extract_section(script_text, "적용"), "duration": 7},
            "cta": {"content": self._extract_section(script_text, "CTA"), "duration": 3},
            "full_script": script_text
        }

    def _extract_section(self, script_text, section_name):
        lines = script_text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            elif in_section and any(word in line.lower() for word in ["후크", "맥락", "설명", "적용", "cta"]):
                break
            elif in_section:
                section_content.append(line.strip())
        
        return ' '.join(section_content).strip() or f"{section_name} 내용 생성됨"
