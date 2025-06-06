import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import logging
from pathlib import Path
import sys

# 프로젝트 루트에서 templates 모듈 import
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from templates import ResearchVideoTemplate

class TitleCardGenerator:
    def __init__(self):
        self.template = ResearchVideoTemplate()
        
        # 한글 폰트 설정
        import matplotlib.font_manager as fm
        
        font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'backend', 'fonts')
        korean_font_path = os.path.join(font_dir, 'NanumGothic.ttf')
        
        if not os.path.exists(korean_font_path):
            korean_font_path = 'C:/Windows/Fonts/malgun.ttf'  # Windows 기본 한글 폰트
        
        try:
            if os.path.exists(korean_font_path):
                # 폰트 파일이 존재할 경우 등록
                font_prop = fm.FontProperties(fname=korean_font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
                logging.info(f"Title generator font loaded from file: {korean_font_path}")
            else:
                raise FileNotFoundError("Font file not found")
        except Exception as e:
            logging.error(f"Matplotlib font loading failed: {e}")
            # 시스템 폰트 사용
            try:
                plt.rcParams['font.family'] = 'Malgun Gothic'
                logging.info("Using system font: Malgun Gothic")
            except:
                try:
                    plt.rcParams['font.family'] = 'NanumGothic'
                    logging.info("Using system font: NanumGothic")
                except:
                    plt.rcParams['font.family'] = 'DejaVu Sans'
                    logging.info("Using fallback font: DejaVu Sans")
        
        plt.rcParams['axes.unicode_minus'] = False
        
    def generate(self, title, subtitle, output_path):
        logging.info(f"Generating research template for: {title[:30]}...")
        
        if not title or not subtitle:
            raise ValueError("ERROR: Title and subtitle required for template generation")
        
        # 논문 메타데이터 추출
        paper_title = title[:60] if len(title) > 60 else title
        author = "Research Team (AI Institute)"
        date = "2024.06.04"
        hashtags = "#AIResearch #Science"
        
        # 컨텐츠 이미지 생성 (서브타이틀을 컨텐츠로 사용)
        content_img_path = output_path.replace('.png', '_content.png')
        self._create_content_image(subtitle, content_img_path)
        
        # 템플릿 생성
        template_img = self.template.CreateTemplate(
            paper_title, author, date, hashtags, content_img_path
        )
        
        # 저장
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        template_img.save(output_path)
        
        # 파일 생성 검증
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"ERROR: Template not created: {output_path}")
            
        file_size = os.path.getsize(output_path)
        if file_size < 1000:
            raise ValueError(f"ERROR: Template file too small ({file_size} bytes)")
        
        logging.info(f"Research template generated: {output_path} ({file_size} bytes)")
        return output_path
    
    def _create_content_image(self, content_text, output_path):
        """컨텐츠 영역용 이미지 생성"""
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (1020, 1420), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', 'fonts')
            korean_font_path = os.path.join(font_dir, 'NanumGothic.ttf')
            if not os.path.exists(korean_font_path):
                korean_font_path = 'C:/Windows/Fonts/malgun.ttf'
            font = ImageFont.truetype(korean_font_path, 40)
            logging.info(f"Content font loaded: {korean_font_path}")
        except Exception as e:
            logging.error(f"Content font loading failed: {e}")
            font = ImageFont.load_default()
        
        # 텍스트 줄바꿈
        lines = self._wrap_text(content_text, 25)
        
        y = 100
        for line in lines[:15]:
            draw.text((50, y), line, fill='black', font=font)
            y += 70
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        
        logging.info(f"Content image created: {output_path}")
    
    def _wrap_text(self, text, max_length):
        """텍스트를 지정된 길이로 줄바꿈"""
        if not text:
            return ['']
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_length:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
