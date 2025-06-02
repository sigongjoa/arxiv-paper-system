import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import logging

class TitleCardGenerator:
    def __init__(self):
        # 한글 폰트 설정 (시스템에 따라 다를 수 있음)
        try:
            # Windows 기본 한글 폰트 시도
            plt.rcParams['font.family'] = 'Malgun Gothic'
        except:
            try:
                plt.rcParams['font.family'] = 'NanumGothic'
            except:
                plt.rcParams['font.family'] = 'DejaVu Sans'
        
        plt.rcParams['axes.unicode_minus'] = False
        
    def generate(self, title, subtitle, output_path):
        try:
            # 9:16 비율 (세로형)
            fig, ax = plt.subplots(figsize=(10.8, 19.2))  # 1080x1920 비율
            fig.patch.set_facecolor('#1a1a1a')
            ax.set_facecolor('#1a1a1a')
            
            # 제목 텍스트 (여러 줄 처리)
            title_lines = self._wrap_text(title, 30)
            title_text = '\n'.join(title_lines)
            
            ax.text(0.5, 0.7, title_text, 
                   transform=ax.transAxes,
                   fontsize=32, 
                   color='white',
                   ha='center',
                   va='center',
                   weight='bold',
                   linespacing=1.5)
                   
            # 부제목 텍스트 (여러 줄 처리)
            subtitle_lines = self._wrap_text(subtitle, 40)
            subtitle_text = '\n'.join(subtitle_lines)
            
            ax.text(0.5, 0.3, subtitle_text,
                   transform=ax.transAxes,
                   fontsize=20,
                   color='#cccccc',
                   ha='center',
                   va='center',
                   linespacing=1.4)
            
            # 장식 요소 추가
            ax.axhline(y=0.5, xmin=0.1, xmax=0.9, color='#4CAF50', linewidth=3, alpha=0.7)
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=100, bbox_inches='tight', 
                       facecolor='#1a1a1a', edgecolor='none')
            plt.close()
            
            logging.info(f"Title card generated: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Title card error: {e}")
            raise
    
    def _wrap_text(self, text, max_length):
        """텍스트를 지정된 길이로 줄바꿈"""
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
