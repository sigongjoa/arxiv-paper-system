import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from backend.lm_studio_client import LMStudioClient
from backend.paper_analyzer import PaperAnalyzer
from backend.core.shorts.hook_generator import HookGenerator
import logging

class ScriptGeneratorImpl:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.client = LMStudioClient(base_url)
        self.analyzer = PaperAnalyzer()
        self.hook_generator = HookGenerator()
        
    def generate_script(self, summary_data, paper_data):
        logging.info(f"ERROR 레벨: Generating mass-production shorts script for {paper_data.get('title', 'Unknown')}")
        
        if not paper_data or not summary_data:
            raise ValueError("ERROR: Paper data and summary required for script generation")
            
        # 실제 논문 내용 추출 (필수)
        pdf_stream = self.analyzer.download_pdf(paper_data['arxiv_id'])
        full_text = self.analyzer.extract_pdf_text(pdf_stream)
        results_section = self.analyzer.find_results_section(full_text)
        
        if not results_section:
            raise ValueError(f"ERROR: Cannot extract results section from paper {paper_data['arxiv_id']}")
            
        # 양산형 쇼츠용 훅 생성
        hook = self.hook_generator.generate(paper_data)
        
        # 60초 제한 엄격 적용
        enhanced_summary = f"""
제목: {paper_data['title']}
요약: {summary_data}
주요 결과: {results_section[:500]}
"""
        
        script_data = self.client.generate_shorts_script(enhanced_summary, paper_data, hook)
        
        # paper_id 추가 (고유 파일명 생성용)
        script_data['paper_id'] = paper_data['arxiv_id']
        
        # 60초 초과 검증
        total_duration = sum(scene.get('duration', 0) for scene in script_data.get('scenes', []))
        if total_duration > 60:
            raise ValueError(f"ERROR: Script duration {total_duration}s exceeds 60s limit")
            
        logging.info(f"Generated unique shorts script: {paper_data['arxiv_id']} - {len(script_data.get('scenes', []))} scenes, {total_duration}s total")
        return script_data
