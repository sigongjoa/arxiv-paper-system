import requests
import xml.etree.ElementTree as ET
import logging
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pymupdf
import io
import base64
from PIL import Image

class ProcessorImpl:
    def __init__(self):
        # HTTP 세션 설정 (재시도 로직 포함)
        self.session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 연결 타임아웃 설정
        self.session.headers.update({
            'User-Agent': 'arXiv-to-Shorts/1.0 (https://github.com/example/arxiv-to-shorts)'
        })
        
    def process_arxiv_paper(self, arxiv_id):
        logging.info(f"ERROR 레벨: Starting figure-based processing for arXiv ID: {arxiv_id}")
        clean_id = arxiv_id.replace('v1', '').replace('v2', '').replace('v3', '')
        
        # 메타데이터 가져오기
        paper_metadata = self._fetch_paper_metadata(clean_id)
        
        # PDF 다운로드 및 그림 추출
        figures_data = self._extract_figures_from_pdf(clean_id)
        
        # 해시태그 생성
        hashtags = self._generate_hashtags(paper_metadata['categories'], paper_metadata['title'])
        
        # 그림 기반 대본 생성을 위한 데이터 구성
        paper_dict = {
            'arxiv_id': paper_metadata['arxiv_id'],
            'title': paper_metadata['title'],
            'abstract': paper_metadata['abstract'],
            'authors': paper_metadata['authors'],
            'categories': paper_metadata['categories'],
            'hashtags': hashtags,
            'figures': figures_data['figures'],
            'figure_count': len(figures_data['figures'])
        }
        
        logging.info(f"Successfully processed paper with {len(figures_data['figures'])} figures: {paper_metadata['title']}")
        
        return {
            'paper': paper_dict,
            'summary': paper_metadata['abstract'],
            'status': 'completed'
        }
    
    def _fetch_paper_metadata(self, clean_id):
        """ArXiv API에서 논문 메타데이터 가져오기"""
        logging.info(f"ERROR 레벨: Fetching paper metadata from arXiv API...")
        url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
        
        max_retries = 3
        for attempt in range(max_retries):
            logging.info(f"arXiv API request attempt {attempt + 1}/{max_retries}")
            response = self.session.get(url, timeout=(10, 30))
            
            if response.status_code == 200:
                break
            else:
                logging.warning(f"arXiv API returned status {response.status_code}")
                if attempt == max_retries - 1:
                    raise Exception(f"arXiv API error: {response.status_code}")
            time.sleep(2 ** attempt)
        
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entries = root.findall('atom:entry', ns)
        if not entries:
            logging.error(f"Paper {clean_id} not found")
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
        
        return {
            'arxiv_id': paper_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'categories': categories
        }
    
    def _extract_figures_from_pdf(self, arxiv_id):
        """PDF에서 그림 추출 및 분석"""
        logging.info(f"ERROR 레벨: Extracting figures from PDF for {arxiv_id}")
        
        # ArXiv PDF URL
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        # PDF 다운로드
        response = self.session.get(pdf_url, timeout=30)
        if response.status_code != 200:
            raise Exception(f"PDF download failed: {response.status_code}")
        
        # PyMuPDF로 PDF 처리
        pdf_document = pymupdf.open(stream=response.content, filetype="pdf")
        total_pages = len(pdf_document)  # 미리 저장
        figures = []
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            
            # 페이지에서 이미지 추출
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                
                # 이미지 크기 확인 (너무 작은 이미지 제외)
                if len(image_bytes) < 5000:  # 5KB 미만 제외
                    continue
                
                # PIL Image로 변환
                image = Image.open(io.BytesIO(image_bytes))
                
                # 이미지 크기 확인 (픽셀 기준)
                if image.width < 100 or image.height < 100:
                    continue
                
                # OCR 제거 - 빈 문자열로 대체
                extracted_text = ""
                
                # 이미지를 base64로 인코딩 (나중에 사용할 수 있도록)
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                
                # 페이지 텍스트에서 관련 캡션 찾기
                page_text = page.get_text()
                figure_caption = self._find_figure_caption(page_text, img_index, page_num)
                
                figures.append({
                    'page': page_num + 1,
                    'index': img_index,
                    'width': image.width,
                    'height': image.height,
                    'size_bytes': len(image_bytes),
                    'extracted_text': extracted_text,
                    'caption': figure_caption,
                    'image_base64': img_base64,
                    'figure_type': self._classify_figure_type(extracted_text, figure_caption)
                })
                
                logging.info(f"Extracted figure {len(figures)} from page {page_num + 1}")
        
        pdf_document.close()
        
        # 그림들을 중요도 순으로 정렬 (크기, 텍스트 내용 기반)
        figures = self._rank_figures_by_importance(figures)
        
        logging.info(f"Successfully extracted {len(figures)} figures")
        
        return {
            'figures': figures,
            'total_pages': total_pages
        }
    
    def _find_figure_caption(self, page_text, img_index, page_num):
        """페이지 텍스트에서 그림 캡션 찾기"""
        # 일반적인 그림 캡션 패턴 찾기
        import re
        
        # Figure X, Fig. X, Table X 등의 패턴
        patterns = [
            r'Figure\s+\d+[:.]\s*([^\n]+)',
            r'Fig\.\s*\d+[:.]\s*([^\n]+)',
            r'Table\s+\d+[:.]\s*([^\n]+)',
            r'Algorithm\s+\d+[:.]\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # 첫 번째 매치를 사용 (더 정교한 로직 필요시 개선)
                return matches[0].strip()
        
        return ""
    
    def _classify_figure_type(self, extracted_text, caption):
        """그림 유형 분류 (캡션 기반)"""
        text_content = caption.lower()
        
        # 키워드 기반 분류
        if any(word in text_content for word in ['table', 'dataset', 'results']):
            return 'table'
        elif any(word in text_content for word in ['algorithm', 'procedure', 'flowchart']):
            return 'flowchart'
        elif any(word in text_content for word in ['accuracy', 'loss', 'performance', 'score']):
            return 'performance_plot'
        elif any(word in text_content for word in ['architecture', 'model', 'network']):
            return 'architecture_diagram'
        elif any(word in text_content for word in ['comparison', 'vs', 'versus']):
            return 'comparison_chart'
        else:
            return 'figure'
    
    def _rank_figures_by_importance(self, figures):
        """그림들을 중요도 순으로 정렬"""
        def calculate_importance_score(fig):
            score = 0
            
            # 크기 점수 (큰 이미지에 가중치)
            score += min(fig['width'] * fig['height'] / 10000, 10)
            
            # 캡션 내용 점수
            text_content = fig['caption']
            important_keywords = ['result', 'performance', 'accuracy', 'comparison', 'architecture', 'model']
            score += sum(2 for keyword in important_keywords if keyword in text_content.lower())
            
            # 캡션 길이 점수 (적절한 캡션이 있는 경우)
            if 10 < len(fig['caption']) < 200:
                score += 3
            
            return score
        
        # 중요도 점수로 정렬
        figures.sort(key=calculate_importance_score, reverse=True)
        
        # 최대 5개 그림만 선택 (쇼츠 형태에 적합)
        return figures[:5]
    
    def _generate_hashtags(self, categories, title):
        """카테고리와 제목 기반 해시태그 생성"""
        hashtags = []
        
        # 카테고리 기반 해시태그 매핑
        category_map = {
            'cs.AI': ['#AI', '#인공지능', '#ArtificialIntelligence'],
            'cs.LG': ['#MachineLearning', '#머신러닝', '#ML'],
            'cs.CL': ['#NLP', '#자연어처리', '#NaturalLanguage'],
            'cs.CV': ['#ComputerVision', '#컴퓨터비전', '#CV'],
            'stat.ML': ['#Statistics', '#통계', '#ML'],
            'cs.IR': ['#InformationRetrieval', '#정보검색'],
            'cs.DC': ['#DistributedComputing', '#분산컴퓨팅'],
            'cs.NE': ['#NeuralNetworks', '#신경망'],
            'cs.CR': ['#Cryptography', '#암호학'],
            'cs.DB': ['#Database', '#데이터베이스'],
            'cs.HC': ['#HCI', '#HumanComputer'],
            'cs.SE': ['#SoftwareEngineering', '#소프트웨어공학']
        }
        
        # 카테고리 기반 해시태그 추가
        for category in categories:
            if category in category_map:
                hashtags.extend(category_map[category][:2])
        
        # 제목 기반 키워드 추출
        title_lower = title.lower()
        keyword_map = {
            'deep': '#DeepLearning',
            'neural': '#Neural',
            'transformer': '#Transformer', 
            'attention': '#Attention',
            'language': '#Language',
            'vision': '#Vision',
            'rag': '#RAG',
            'llm': '#LLM',
            'bert': '#BERT',
            'gpt': '#GPT',
            'diffusion': '#Diffusion',
            'gan': '#GAN',
            'reinforcement': '#RL',
            'quantum': '#Quantum',
            'blockchain': '#Blockchain',
            'embedding': '#Embedding',
            'optimization': '#Optimization',
            'graph': '#Graph',
            'recommendation': '#Recommendation'
        }
        
        for keyword, tag in keyword_map.items():
            if keyword in title_lower:
                hashtags.append(tag)
        
        # 기본 해시태그 추가
        hashtags.extend(['#ArXiv', '#연구논문', '#학술'])
        
        # 중복 제거 및 최대 10개로 제한
        unique_hashtags = list(dict.fromkeys(hashtags))
        return unique_hashtags[:10]
