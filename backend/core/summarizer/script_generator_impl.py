import sys
import os

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from backend.lm_studio_client import LMStudioClient
from backend.paper_analyzer import PaperAnalyzer
import logging

class ScriptGeneratorImpl:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.client = LMStudioClient(base_url)
        self.analyzer = PaperAnalyzer()
        
    def generate_script(self, summary_data, paper_data):
        try:
            # 실제 논문 내용 추출
            try:
                pdf_stream = self.analyzer.download_pdf(paper_data['arxiv_id'])
                full_text = self.analyzer.extract_pdf_text(pdf_stream)
                
                # 결론/결과 섹션 추출
                results_section = self.analyzer.find_results_section(full_text)
                
                # 전체 내용과 결과를 합쳐 요약 데이터 생성
                enhanced_summary = f"""
제목: {paper_data['title']}
요약: {summary_data}

주요 결과:
{results_section[:500]}
"""
                
                logging.info(f"Using enhanced content with results section")
                
            except Exception as e:
                logging.warning(f"Failed to get full content, using summary: {e}")
                enhanced_summary = summary_data
            
            return self.client.generate_script(enhanced_summary, paper_data)
            
        except Exception as e:
            logging.error(f"Script generation error: {e}")
            # 에러 시 기본 스크립트 반환
            title = paper_data.get('title', 'Unknown Paper')[:40]
            return {
                "hook": f"새로운 연구 발견: {title}...",
                "scenes": [
                    {"text": f"오늘 소개할 논문은 '{title}' 입니다.", "duration": 10, "visual": "title_card"},
                    {"text": "이 연구는 혁신적인 접근법을 제시합니다.", "duration": 15, "visual": "diagram"},
                    {"text": "실험 결과는 놀라운 성능 향상을 보여줍니다.", "duration": 15, "visual": "chart"},
                    {"text": "이 연구가 미래에 미칠 영향은 상당할 것입니다.", "duration": 15, "visual": "conclusion"}
                ],
                "cta": "더 많은 AI 연구 소식을 구독해주세요!"
            }
