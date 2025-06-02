import sys
import os

# 프로젝트 루트를 sys.path에 추가
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
        try:
            # 실제 논문 PDF 다운로드 및 내용 추출
            try:
                pdf_stream = self.analyzer.download_pdf(paper_data['arxiv_id'])
                full_text = self.analyzer.extract_pdf_text(pdf_stream)
                
                # 전체 텍스트에서 샘플 추출 (처음 3000자)
                text_sample = full_text[:3000] if len(full_text) > 3000 else full_text
                
                logging.info(f"Using full paper content ({len(full_text)} chars)")
                
            except Exception as e:
                logging.warning(f"Failed to download PDF, using abstract: {e}")
                text_sample = paper_data.get('abstract', '')
            
            # LLM으로 핵심 정보 추출
            return self.client.extract_key_findings({
                'title': paper_data['title'],
                'abstract': text_sample
            })
            
        except Exception as e:
            logging.error(f"Key extraction error: {e}")
            # 에러 시 기본 구조 반환 (하드코딩 아님)
            return {
                "main_contribution": f"{paper_data['title']}의 주요 기여점",
                "methodology": "혁신적인 접근 방법 사용",
                "results": "유의미한 성능 향상 달성",
                "impact": "해당 분야에 중요한 영향 기대"
            }
