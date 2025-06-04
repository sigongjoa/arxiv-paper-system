import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import logging

class TitleCardGenerator:
    def __init__(self):
        # 한글 폰트 설정 - 환경변수 우선
        font_name = os.getenv('TITLE_FONT', 'Malgun Gothic')
        
        try:
            plt.rcParams['font.family'] = font_name
            logging.info(f"Using font: {font_name}")
        except Exception as e:
            raise ValueError(f"ERROR: Font '{font_name}' not available. Set TITLE_FONT environment variable to a valid font name: {e}")
        
        plt.rcParams['axes.unicode_minus'] = False
        
    def generate(self, title, subtitle, output_path):
        logging.info(f"ERROR 레벨: Generating 9:16 title card for: {title[:30]}...")
        
        if not title or not subtitle:
            raise ValueError("ERROR: Title and subtitle required for title card generation")
        
        # 9:16 비율 (세로형 쇼츠 최적화)
        fig, ax = plt.subplots(figsize=(6, 10.67))  # 1080x1920 비율
        fig.patch.set_facecolor('#000000')  # 완전한 검은색
        ax.set_facecolor('#000000')
        
        # 제목 텍스트 (여러 줄 처리)
        title_lines = self._wrap_text(title, 25)  # 모바일 최적화 단축
        title_text = '\\n'.join(title_lines)
        
        ax.text(0.5, 0.75, title_text, 
               transform=ax.transAxes,
               fontsize=36,  # 모바일용 큰 폰트
               color='white',
               ha='center',
               va='center',
               weight='bold',
               linespacing=1.3)
               
        # 부제목 텍스트 (여러 줄 처리)
        subtitle_lines = self._wrap_text(subtitle, 35)
        subtitle_text = '\\n'.join(subtitle_lines)
        
        ax.text(0.5, 0.25, subtitle_text,
               transform=ax.transAxes,
               fontsize=24,  # 모바일용 조정
               color='#FFFFFF',
               ha='center',
               va='center',
               linespacing=1.2)
        
        # 양산형 쇼츠 스타일 - 네온 라인
        ax.axhline(y=0.5, xmin=0.1, xmax=0.9, color='#00FF88', linewidth=4, alpha=0.8)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='#000000', edgecolor='none')
        plt.close()
        
        # 파일 생성 검증
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"ERROR: Title card not created: {output_path}")
            
        file_size = os.path.getsize(output_path)
        if file_size < 1000:
            raise ValueError(f"ERROR: Title card file too small ({file_size} bytes)")
        
        logging.info(f"9:16 title card generated: {output_path} ({file_size} bytes)")
        return output_path
    
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
