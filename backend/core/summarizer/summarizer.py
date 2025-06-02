from .script_generator import LocalLLMClient
from .key_extractor import KeyExtractor
import logging

class Summarizer:
    def __init__(self):
        self.script_generator = LocalLLMClient()
        self.key_extractor = KeyExtractor()
        
    def generate_script(self, paper_data):
        try:
            # 핵심 정보 추출
            key_findings = self.key_extractor.extract(paper_data)
            
            # 요약 데이터 준비
            summary_data = f"""
주요 기여점: {key_findings['main_contribution']}
방법론: {key_findings['methodology']}
결과: {key_findings['results']}
영향: {key_findings['impact']}
"""
            
            script = self.script_generator.generate_script(summary_data, paper_data)
            script['paper_id'] = paper_data.get('arxiv_id', 'unknown')
            
            return script
            
        except Exception as e:
            logging.error(f"Summarization error: {e}")
            raise
