import requests
import xml.etree.ElementTree as ET
import logging
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import io
import base64

import pymupdf
PYMUPDF_AVAILABLE = True

from PIL import Image
PIL_AVAILABLE = True

class ProcessorImplDebug:
    def __init__(self):
        # HTTP 세션 설정
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'arXiv-to-Shorts/1.0 (debug)'
        })
        
    def process_arxiv_paper(self, arxiv_id):
        logging.error(f"DEBUG: Starting figure extraction for arXiv ID: {arxiv_id}")
        clean_id = arxiv_id.replace('v1', '').replace('v2', '').replace('v3', '')
        
        # 라이브러리 체크
        if not PYMUPDF_AVAILABLE:
            logging.error("ERROR: PyMuPDF not available - falling back to no figures")
            return self._fallback_no_figures(clean_id)
        
        if not PIL_AVAILABLE:
            logging.error("ERROR: PIL not available - falling back to no figures")
            return self._fallback_no_figures(clean_id)
        
        # 메타데이터 가져오기
        paper_metadata = self._fetch_paper_metadata(clean_id)
        
        # PDF 다운로드 및 그림 추출 (디버그 모드)
        figures_data = self._extract_figures_from_pdf_debug(clean_id)
        
        # 결과 구성
        paper_dict = {
            'arxiv_id': paper_metadata['arxiv_id'],
            'title': paper_metadata['title'],
            'abstract': paper_metadata['abstract'],
            'authors': paper_metadata['authors'],
            'categories': paper_metadata['categories'],
            'figures': figures_data['figures'],
            'figure_count': len(figures_data['figures'])
        }
        
        logging.error(f"DEBUG: Final result - {len(figures_data['figures'])} figures extracted")
        
        return {
            'paper': paper_dict,
            'summary': paper_metadata['abstract'],
            'status': 'completed'
        }
    
    def _fallback_no_figures(self, clean_id):
        """라이브러리 없을 때 폴백"""
        paper_metadata = self._fetch_paper_metadata(clean_id)
        
        paper_dict = {
            'arxiv_id': paper_metadata['arxiv_id'],
            'title': paper_metadata['title'],
            'abstract': paper_metadata['abstract'],
            'authors': paper_metadata['authors'],
            'categories': paper_metadata['categories'],
            'figures': [],
            'figure_count': 0
        }
        
        return {
            'paper': paper_dict,
            'summary': paper_metadata['abstract'],
            'status': 'completed_no_figures'
        }
    
    def _fetch_paper_metadata(self, clean_id):
        """ArXiv API에서 논문 메타데이터 가져오기"""
        logging.error(f"DEBUG: Fetching metadata for {clean_id}")
        url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
        
        response = self.session.get(url, timeout=(10, 30))
        if response.status_code != 200:
            raise Exception(f"arXiv API error: {response.status_code}")
        
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entries = root.findall('atom:entry', ns)
        if not entries:
            raise Exception(f"Paper {clean_id} not found in arXiv")
        
        entry = entries[0]
        
        paper_id = entry.find('atom:id', ns).text.split('/')[-1]
        title = entry.find('atom:title', ns).text.strip()
        abstract = entry.find('atom:summary', ns).text.strip()
        
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns).text
            authors.append(name)
        
        categories = []
        for category in entry.findall('atom:category', ns):
            categories.append(category.get('term'))
        
        logging.error(f"DEBUG: Metadata OK - Title: {title[:50]}...")
        return {
            'arxiv_id': paper_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'categories': categories
        }
    
    def _extract_figures_from_pdf_debug(self, arxiv_id):
        """PDF에서 그림 추출 (디버그 모드 - 완화된 필터링)"""
        logging.error(f"DEBUG: Starting PDF figure extraction for {arxiv_id}")
        
        # PDF 다운로드
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        logging.error(f"DEBUG: Downloading PDF from {pdf_url}")
        
        response = self.session.get(pdf_url, timeout=30)
        if response.status_code != 200:
            raise Exception(f"PDF download failed: {response.status_code}")
        
        logging.error(f"DEBUG: PDF downloaded - {len(response.content)} bytes")
        
        # PyMuPDF로 PDF 처리
        pdf_document = pymupdf.open(stream=response.content, filetype="pdf")
        total_pages = len(pdf_document)  # 미리 저장
        logging.error(f"DEBUG: PDF opened - {total_pages} pages")
        
        figures = []
        total_images_found = 0
        
        # 처음 10페이지만 스캔 (시간 절약)
        max_pages = min(10, total_pages)
        
        for page_num in range(max_pages):
            page = pdf_document[page_num]
            image_list = page.get_images()
            total_images_found += len(image_list)
            
            logging.error(f"DEBUG: Page {page_num + 1}: {len(image_list)} images found")
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                
                logging.error(f"DEBUG: Image {img_index + 1} - {len(image_bytes)} bytes")
                
                # 완화된 필터링: 1KB 이상만 (원래 5KB)
                if len(image_bytes) < 1000:
                    logging.error(f"DEBUG: Skipped - too small (<1KB)")
                    continue
                
                # PIL Image로 변환
                image = Image.open(io.BytesIO(image_bytes))
                logging.error(f"DEBUG: Image size: {image.width}x{image.height}")
                
                # 완화된 픽셀 필터링: 50x50 이상만 (원래 100x100)
                if image.width < 50 or image.height < 50:
                    logging.error(f"DEBUG: Skipped - too small (<50px)")
                    continue
                
                # base64 인코딩
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                
                # 페이지 텍스트에서 캡션 찾기
                page_text = page.get_text()
                figure_caption = self._find_figure_caption_debug(page_text, img_index, page_num)
                
                figures.append({
                    'page': page_num + 1,
                    'index': img_index,
                    'width': image.width,
                    'height': image.height,
                    'size_bytes': len(image_bytes),
                    'extracted_text': "",
                    'caption': figure_caption,
                    'image_base64': img_base64,
                    'figure_type': self._classify_figure_type(figure_caption)
                })
                
                logging.error(f"DEBUG: ✓ Added figure {len(figures)} from page {page_num + 1}")
                logging.error(f"DEBUG: Caption: {figure_caption[:100]}")
        
        pdf_document.close()
        
        logging.error(f"DEBUG: Extraction summary:")
        logging.error(f"  - Total images found: {total_images_found}")
        logging.error(f"  - Valid figures extracted: {len(figures)}")
        logging.error(f"  - Pages scanned: {max_pages}")
        
        return {
            'figures': figures[:5],  # 최대 5개만
            'total_pages': total_pages
        }
    
    def _find_figure_caption_debug(self, page_text, img_index, page_num):
        """페이지 텍스트에서 그림 캡션 찾기 (디버그 모드)"""
        import re
        
        # 다양한 캡션 패턴
        patterns = [
            r'Figure\s+(\d+)[:.](.*?)(?=\n|Figure|Table|$)',
            r'Fig\.\s*(\d+)[:.](.*?)(?=\n|Fig\.|Table|$)',
            r'Table\s+(\d+)[:.](.*?)(?=\n|Figure|Table|$)',
            r'Algorithm\s+(\d+)[:.](.*?)(?=\n|Algorithm|Figure|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if matches:
                # 첫 번째 매치의 설명 부분 반환
                if len(matches[0]) > 1:
                    caption = matches[0][1].strip()
                    # 긴 캡션은 잘라내기
                    if len(caption) > 200:
                        caption = caption[:200] + "..."
                    return caption
        
        # 캡션이 없으면 기본값
        return f"Figure from page {page_num + 1}"
    
    def _classify_figure_type(self, caption):
        """그림 유형 분류"""
        text_content = caption.lower()
        
        if any(word in text_content for word in ['table', 'dataset']):
            return 'table'
        elif any(word in text_content for word in ['algorithm', 'procedure']):
            return 'flowchart'
        elif any(word in text_content for word in ['accuracy', 'loss', 'performance']):
            return 'performance_plot'
        elif any(word in text_content for word in ['architecture', 'model', 'network']):
            return 'architecture_diagram'
        else:
            return 'figure'
