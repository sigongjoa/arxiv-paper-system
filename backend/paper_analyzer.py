import requests
import PyPDF2
import io
import logging
import re
import json

class PaperAnalyzer:
    def __init__(self):
        self.base_url = "http://127.0.0.1:1234"
        
    def download_pdf(self, arxiv_id):
        clean_id = arxiv_id.replace('v1', '').replace('v2', '').replace('v3', '')
        pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        
        response = requests.get(pdf_url)
        if response.status_code != 200:
            logging.error(f"PDF download failed: {response.status_code}")
            raise Exception(f"PDF download failed: {response.status_code}")
            
        return io.BytesIO(response.content)
    
    def extract_pdf_text(self, pdf_stream):
        reader = PyPDF2.PdfReader(pdf_stream)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        return text
    
    def find_results_section(self, full_text):
        patterns = [
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:experimental\s+)?results?\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?evaluation\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?experiments?\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?performance\s*(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                start = match.end()
                end = min(start + 2000, len(full_text))
                return full_text[start:end]
        
        mid = len(full_text) // 2
        return full_text[mid:mid+1500]
    
    def extract_performance_data(self, paper_data):
        try:
            pdf_stream = self.download_pdf(paper_data['arxiv_id'])
            full_text = self.extract_pdf_text(pdf_stream)
            results_section = self.find_results_section(full_text)
            
            prompt = f"""논문의 결과 섹션에서 성능 수치를 추출하세요.

제목: {paper_data['title']}
결과 섹션:
{results_section[:1000]}

다음 JSON 형식으로만 응답하세요:
{{
  "baseline_performance": 숫자,
  "proposed_performance": 숫자,
  "metric_name": "정확도",
  "improvement": 숫자,
  "has_valid_data": true
}}"""

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 300
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                
                try:
                    return json.loads(content.strip())
                except json.JSONDecodeError:
                    return self._direct_number_extraction(results_section)
            else:
                return self._direct_number_extraction(results_section)
                
        except Exception as e:
            logging.error(f"Performance data extraction failed: {e}")
            return self._direct_number_extraction(paper_data.get('abstract', ''))
    
    def _direct_number_extraction(self, text):
        patterns = [
            r'(\d+(?:\.\d+)?)\s*%\s*(?:accuracy|precision|recall|f1)',
            r'(?:accuracy|precision|recall|f1).*?(\d+(?:\.\d+)?)\s*%',
            r'(?:from|baseline).*?(\d+(?:\.\d+)?).*?(?:to|ours|proposed).*?(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*vs\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*→\s*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                if len(matches[0]) == 2:
                    baseline, proposed = matches[0]
                    return {
                        "baseline_performance": float(baseline),
                        "proposed_performance": float(proposed),
                        "metric_name": "성능",
                        "improvement": float(proposed) - float(baseline),
                        "has_valid_data": True
                    }
                elif len(matches) >= 2:
                    values = [float(m) if isinstance(m, str) else float(m[0]) for m in matches[:2]]
                    return {
                        "baseline_performance": min(values),
                        "proposed_performance": max(values),
                        "metric_name": "성능",
                        "improvement": max(values) - min(values),
                        "has_valid_data": True
                    }
        
        return {
            "baseline_performance": 0,
            "proposed_performance": 0,
            "metric_name": "성능",
            "improvement": 0,
            "has_valid_data": False
        }
