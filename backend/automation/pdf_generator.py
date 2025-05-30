import logging
from typing import Dict, List
import tempfile
import os
import subprocess

logger = logging.getLogger(__name__)

class PdfGenerator:
    def __init__(self, headless: bool = True):
        self.headless = headless
        logger.info("DEBUG: PdfGenerator initialized")
    
    def generate_from_papers(self, papers: List[Dict], title: str = "arXiv Newsletter") -> bytes:
        html_content = self._generate_html_content(papers, title)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_file:
            html_file.write(html_content)
            html_path = html_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
            pdf_path = pdf_file.name
        
        try:
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '20mm',
                '--margin-bottom', '20mm', 
                '--margin-left', '15mm',
                '--margin-right', '15mm',
                '--encoding', 'UTF-8',
                html_path, pdf_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"ERROR: wkhtmltopdf failed: {result.stderr}")
                raise Exception(f"PDF generation failed: {result.stderr}")
            
            with open(pdf_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
            
            logger.info(f"DEBUG: PDF generated, size: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"ERROR: PDF generation failed: {str(e)}", exc_info=True)
            raise
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    def _generate_html_content(self, papers: List[Dict], title: str) -> str:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
                .paper {{ margin-bottom: 30px; padding: 15px; border-left: 3px solid #007acc; }}
                .title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 8px; }}
                .authors {{ color: #666; margin-bottom: 5px; }}
                .categories {{ color: #888; font-size: 12px; margin-bottom: 10px; }}
                .summary {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>Total Papers: {len(papers)}</p>
            </div>
        """
        
        for i, paper in enumerate(papers, 1):
            html += f"""
            <div class="paper">
                <div class="title">{i}. {paper.get('title', 'No Title')}</div>
                <div class="authors">Authors: {', '.join(paper.get('authors', []))}</div>
                <div class="categories">Categories: {', '.join(paper.get('categories', []))}</div>
                <div class="summary">{paper.get('summary', 'No summary available')}</div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
