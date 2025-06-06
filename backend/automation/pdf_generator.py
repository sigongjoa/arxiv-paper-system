import logging
from typing import Dict, List
import os

logger = logging.getLogger(__name__)

class PdfGenerator:
    def __init__(self, headless: bool = True):
        self.headless = headless
        # 기존 PDF 생성기 가져오기
        from utils.pdf_generator import AIAnalysisPDFGenerator
        self.ai_pdf_generator = AIAnalysisPDFGenerator()
        logger.info("DEBUG: PdfGenerator initialized with Enhanced Template")
    
    def generate_from_papers(self, papers: List[Dict], title: str = "Research Analysis Report") -> bytes:
        """Enhanced 템플릿으로 PDF 생성"""
        try:
            if not papers:
                raise Exception("No papers to generate PDF")
            
            # 첫 번째 논문으로 PDF 생성 (개별 PDF이므로)
            paper = papers[0]
            
            # 기존 방식으로 PDF 생성 (안정성을 위해)
            paper_title = paper.get('title', 'Unknown Title')
            paper_id = paper.get('paper_id', 'unknown')
            if not paper_id or paper_id == 'unknown':
                paper_id = paper_title[:20].replace(' ', '_').replace('/', '_')
            
            # AI 분석 결과를 기존 형식에 맞게 변환
            analysis_data = {
                'background': {
                    'problem_definition': paper.get('summary', ''),
                    'motivation': paper.get('methodology', '')
                },
                'contributions': paper.get('key_insights', []),
                'main_findings': paper.get('main_findings', []),
                'limitations': paper.get('limitations', []),
                'future_work': paper.get('future_work', []),
                'keywords': paper.get('keywords', []),
                'confidence_score': paper.get('confidence_score', 0.0),
                'platform': paper.get('platform', 'Unknown')
            }
            
            # PDF 생성
            pdf_path = self.ai_pdf_generator.generate_analysis_pdf(
                title=paper_title,
                arxiv_id=paper_id,
                analysis=analysis_data
            )
            
            # 생성된 PDF 파일을 바이트로 읽기
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            logger.info(f"DEBUG: PDF generated successfully, size: {len(pdf_bytes)} bytes")
            logger.info(f"DEBUG: PDF saved at: {pdf_path}")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"ERROR: PDF generation failed: {str(e)}", exc_info=True)
            raise
