import os
import json
import logging
import shutil
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import re

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class AIAnalysisPDFGenerator:
    def __init__(self):
        # PDF 출력 디렉토리를 루트 경로의 pdfs/로 직접 설정
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "pdfs")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_analysis_pdf(self, title, arxiv_id, analysis):
        # PDF 생성 전에 출력 디렉토리 정리 (이제 _clear_output_directory 제거되므로 호출도 제거)
        # self._clear_output_directory() 

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = f"analysis_{arxiv_id.replace('/', '_')}_{timestamp}.pdf" # 기존 파일명 로직
        # 논문 제목으로 파일명 생성 (safe_title은 test/integrated_platform_test.py에서 이미 처리)
        # 여기서는 단순히 전달받은 title을 사용하고, pdf_generator.py의 generate_from_papers에서 논문 제목을 사용하도록 처리되었으므로, 해당 인자를 그대로 사용.
        # 만약 title에 문제가 있다면, integrated_platform_test.py에서 정제해야 함.
        safe_title = re.sub(r'[\\/:*?"<>|]', '', title).replace(' ', '_').replace('...', '') # test_platform_integrated에서 잘린 제목 복구 및 추가 정제
        if not safe_title: # 제목이 비어있을 경우 대체값
            safe_title = f"analysis_{arxiv_id.replace('/', '_')}"
        filename = f"{safe_title}_{timestamp}.pdf"

        filepath = os.path.join(self.output_dir, filename)
        
        logging.error(f"PDF 생성: {filepath}")
        logging.error(f"분석 데이터: {json.dumps(analysis, ensure_ascii=False)}")
        
        # 폰트 설정
        font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'src', 'assets', 'fonts', 'NanumGothic-Regular.ttf')
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                font_name = 'NanumGothic'
                logging.error(f"NanumGothic 폰트 로드: {font_path}")
            except Exception as e:
                logging.error(f"NanumGothic 폰트 로드 실패: {e}")
                font_name = 'Helvetica'
        else:
            font_name = 'Helvetica'
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # CSS 스타일 모방한 커스텀 스타일들
        styles = self._create_enhanced_styles(font_name)
        
        story = []
        
        # 헤더 (CSS .pdf-header 스타일 모방)
        story.append(Paragraph(f"🤖 AI 논문 분석 보고서", styles['header_title']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"{title}", styles['main_title']))
        story.append(Spacer(1, 0.1*inch))
        
        # 메타 정보
        if isinstance(analysis, str):
            try:
                analysis_data = json.loads(analysis)
            except:
                analysis_data = {"content": analysis}
        else:
            analysis_data = analysis
            
        meta_info = f"논문 ID: {arxiv_id} | 플랫폼: {analysis_data.get('platform', 'Unknown')} | 신뢰도: {analysis_data.get('confidence_score', 0.0):.2f}"
        story.append(Paragraph(meta_info, styles['meta_info']))
        story.append(Paragraph(f"생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}", styles['meta_info']))
        story.append(Spacer(1, 0.3*inch))
        
        # 분석 섹션들 (CSS .analysis-section 스타일 모방)
        sections = [
            ('📋 연구 배경', 'background'),
            ('💡 핵심 기여도', 'contributions'), 
            ('📊 주요 연구 결과', 'main_findings'),
            ('⚠️ 연구 한계점', 'limitations'),
            ('🚀 향후 연구 방향', 'future_work'),
            ('🏷️ 기술 키워드', 'keywords')
        ]
        
        for section_title, section_key in sections:
            self._add_section(story, styles, section_title, section_key, analysis_data)
        
        # 신뢰도 정보
        confidence = analysis_data.get('confidence_score', 0.0)
        story.append(Paragraph('📊 분석 신뢰도', styles['section_header']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"AI 분석 신뢰도: {confidence:.2f} ({confidence*100:.0f}%)", styles['confidence_text']))
        story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        logging.error(f"PDF 생성 완료: {filepath}")
        
        # Copy to main pdfs directory (제거)
        # try:
        #     self.copy_service.copy_new_pdfs()
        #     logging.error(f"PDF 메인 디렉토리 복사 완료")
        # except Exception as e:
        #     logging.error(f"PDF 복사 실패: {e}")
        
        return filepath
    
    def _create_enhanced_styles(self, font_name):
        """CSS 스타일을 모방한 reportlab 스타일들"""
        styles = getSampleStyleSheet()
        
        # CSS 색상들
        primary_color = HexColor('#007bff')
        success_color = HexColor('#28a745')
        warning_color = HexColor('#ffc107')
        info_color = HexColor('#17a2b8')
        dark_color = HexColor('#2c3e50')
        
        custom_styles = {}
        
        # 헤더 제목 (CSS .pdf-header h1 모방)
        custom_styles['header_title'] = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=20,
            textColor=primary_color,
            alignment=TA_CENTER,
            spaceBefore=12,
            spaceAfter=6
        )
        
        # 메인 제목 (CSS .pdf-header h2 모방)
        custom_styles['main_title'] = ParagraphStyle(
            'MainTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=16,
            textColor=dark_color,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=6
        )
        
        # 메타 정보 (CSS .pdf-header p 모방)
        custom_styles['meta_info'] = ParagraphStyle(
            'MetaInfo',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=3
        )
        
        # 섹션 헤더 (CSS .section-header 모방)
        custom_styles['section_header'] = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            textColor=primary_color,
            spaceBefore=12,
            spaceAfter=8,
            borderWidth=0,
            borderColor=primary_color,
            borderPadding=8
        )
        
        # 인사이트 아이템 (CSS .insight-item 모방)
        custom_styles['insight_item'] = ParagraphStyle(
            'InsightItem',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=HexColor('#0369a1'),
            leftIndent=15,
            spaceBefore=4,
            spaceAfter=4,
            borderWidth=0,
            borderColor=primary_color,
            borderPadding=8
        )
        
        # 연구 결과 아이템 (CSS .finding-item 모방)
        custom_styles['finding_item'] = ParagraphStyle(
            'FindingItem',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=HexColor('#000000'),
            leftIndent=15,
            spaceBefore=4,
            spaceAfter=4
        )
        
        # 한계점 아이템 (CSS .limitation-item 모방)
        custom_styles['limitation_item'] = ParagraphStyle(
            'LimitationItem',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=HexColor('#dc3545'),
            leftIndent=15,
            spaceBefore=4,
            spaceAfter=4
        )
        
        # 키워드 (CSS .keyword-tag 모방)
        custom_styles['keyword_tag'] = ParagraphStyle(
            'KeywordTag',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            textColor=HexColor('#ffffff'),
            backColor=info_color,
            borderWidth=0,
            borderColor=info_color,
            borderRadius=5,
            spaceBefore=2,
            spaceAfter=2,
            leftIndent=5,
            rightIndent=5,
            firstLineIndent=0
        )
        
        # 신뢰도 텍스트 (CSS .confidence-text 모방)
        custom_styles['confidence_text'] = ParagraphStyle(
            'ConfidenceText',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=success_color,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=6
        )
        
        # 저자 스타일 (CSS .author-list 모방)
        custom_styles['author_list'] = ParagraphStyle(
            'AuthorList',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            textColor=HexColor('#555555'),
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=0
        )
        
        # 본문 텍스트 (CSS .pdf-body-text 모방)
        custom_styles['body_text'] = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
            alignment=TA_LEFT
        )

        styles.add(custom_styles['header_title'])
        styles.add(custom_styles['main_title'])
        styles.add(custom_styles['meta_info'])
        styles.add(custom_styles['section_header'])
        styles.add(custom_styles['insight_item'])
        styles.add(custom_styles['finding_item'])
        styles.add(custom_styles['limitation_item'])
        styles.add(custom_styles['keyword_tag'])
        styles.add(custom_styles['confidence_text'])
        styles.add(custom_styles['author_list'])
        styles.add(custom_styles['body_text'])

        return styles

    def _add_section(self, story, styles, section_title, section_key, analysis_data):
        content = analysis_data.get(section_key)
        if content:
            story.append(Paragraph(section_title, styles['section_header']))
            story.append(Spacer(1, 0.1*inch))
            
            if isinstance(content, list):
                for item in content:
                    # 키워드 섹션은 특별히 처리
                    if section_key == 'keywords':
                        story.append(Paragraph(f"<font color='#ffffff'> {item} </font>", styles['keyword_tag']))
                    else:
                        story.append(Paragraph(f"• {item}", styles['insight_item']))
            else:
                story.append(Paragraph(str(content), styles['body_text']))
            story.append(Spacer(1, 0.2*inch)) 