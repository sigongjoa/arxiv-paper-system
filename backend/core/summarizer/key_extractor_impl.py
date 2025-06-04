import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from backend.lm_studio_client import LMStudioClient
from backend.paper_analyzer import PaperAnalyzer
import logging

class KeyExtractorImpl:
    def __init__(self, llm_url="http://127.0.0.1:1234"):
        self.client = LMStudioClient(llm_url)
        self.analyzer = PaperAnalyzer()
        
    def extract(self, paper_data):
        logging.info(f"ERROR 레벨: Extracting key findings for {paper_data.get('arxiv_id')}")
        
        if not paper_data or not paper_data.get('arxiv_id'):
            raise ValueError("ERROR: Invalid paper data - arxiv_id required")
        
        # 실제 논문 PDF 다운로드 및 내용 추출 (필수)
        pdf_stream = self.analyzer.download_pdf(paper_data['arxiv_id'])
        full_text = self.analyzer.extract_pdf_text(pdf_stream)
        
        if not full_text.strip():
            raise ValueError(f"ERROR: No text extracted from PDF {paper_data['arxiv_id']}")
        
        # 전체 텍스트에서 샘플 추출 (처음 3000자)
        text_sample = full_text[:3000] if len(full_text) > 3000 else full_text
        
        logging.info(f"Using full paper content ({len(full_text)} chars)")
        
        # LLM으로 핵심 정보 추출 (필수)
        key_findings = self.client.extract_key_findings({
            'title': paper_data['title'],
            'abstract': text_sample
        })
        
        # 추출된 데이터 검증
        required_fields = ['main_contribution', 'methodology', 'results', 'impact']
        for field in required_fields:
            if not key_findings.get(field):
                raise ValueError(f"ERROR: Missing required field '{field}' from LLM response")
        
        logging.info(f"Successfully extracted key findings: {list(key_findings.keys())}")
        return key_findings
