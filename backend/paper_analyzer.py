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
            raise Exception(f"ERROR: PDF download failed for {arxiv_id}: HTTP {response.status_code}")
            
        return io.BytesIO(response.content)
    
    def extract_pdf_text(self, pdf_stream):
        reader = PyPDF2.PdfReader(pdf_stream)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        if not text.strip():
            raise ValueError("ERROR: No text extracted from PDF")
            
        return text
    
    def find_results_section(self, full_text):
        patterns = [
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:experimental\s+)?results?\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?evaluation\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?experiments?\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?performance\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?analysis\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?discussion\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?findings\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?conclusion\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?implementation\s*(?:\n|$)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?validation\s*(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                start = match.end()
                end = min(start + 2000, len(full_text))
                section = full_text[start:end]
                if section.strip():
                    return section
        
        # 패턴으로 찾지 못하면 논문 중간 부분 반환
        mid_point = len(full_text) // 2
        return full_text[mid_point:mid_point + 2000]
    
    def extract_performance_data(self, paper_data):
        logging.info(f"ERROR 레벨: Extracting performance data for {paper_data.get('arxiv_id')}")
        
        # PDF 다운로드 및 텍스트 추출 (필수)
        pdf_stream = self.download_pdf(paper_data['arxiv_id'])
        full_text = self.extract_pdf_text(pdf_stream)
        results_section = self.find_results_section(full_text)
        
        # LM Studio로 성능 데이터 추출
        prompt = f"""논문의 결과 섹션에서 정확한 성능 수치를 추출하세요.

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
}}

숫자가 없으면 has_valid_data를 false로 설정하세요."""

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
        
        if response.status_code != 200:
            raise Exception(f"ERROR: LM Studio API failed: HTTP {response.status_code}")
            
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # JSON 파싱
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        try:
            perf_data = json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"ERROR: Invalid JSON response from LM Studio: {e}")
        
        # 직접 숫자 추출 시도
        direct_data = self._direct_number_extraction(results_section)
        
        # 두 결과 중 유효한 데이터가 있는 것 선택
        if perf_data.get('has_valid_data'):
            logging.info(f"Using LM Studio extracted data: {perf_data}")
            return perf_data
        elif direct_data.get('has_valid_data'):
            logging.info(f"Using regex extracted data: {direct_data}")
            return direct_data
        else:
            # FALLBACK 완전 제거 - 유효한 데이터 없으면 에러
            raise ValueError(f"ERROR: No valid performance data found in paper {paper_data.get('arxiv_id')}")
    
    def _direct_number_extraction(self, text):
        """정규식으로 성능 수치 직접 추출"""
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
                    baseline_val = float(baseline)
                    proposed_val = float(proposed)
                    
                    # 유효성 검증
                    if 0 <= baseline_val <= 100 and 0 <= proposed_val <= 100:
                        return {
                            "baseline_performance": baseline_val,
                            "proposed_performance": proposed_val,
                            "metric_name": "성능",
                            "improvement": proposed_val - baseline_val,
                            "has_valid_data": True
                        }
                elif len(matches) >= 2:
                    values = [float(m) if isinstance(m, str) else float(m[0]) for m in matches[:2]]
                    if all(0 <= v <= 100 for v in values):
                        return {
                            "baseline_performance": min(values),
                            "proposed_performance": max(values),
                            "metric_name": "성능",
                            "improvement": max(values) - min(values),
                            "has_valid_data": True
                        }
        
        # 유효한 숫자를 찾지 못함
        return {
            "baseline_performance": None,
            "proposed_performance": None,
            "metric_name": None,
            "improvement": None,
            "has_valid_data": False
        }
