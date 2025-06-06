import matplotlib
matplotlib.use('Agg')  # GUI 없는 백엔드 사용
import matplotlib.pyplot as plt
import os
import logging
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from backend.paper_analyzer import PaperAnalyzer

class ChartGeneratorImpl:
    def __init__(self):
        import os
        import matplotlib.font_manager as fm
        
        # 한글 폰트 설정
        font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'backend', 'fonts')
        korean_font_path = os.path.join(font_dir, 'NanumGothic.ttf')
        
        if not os.path.exists(korean_font_path):
            korean_font_path = 'C:/Windows/Fonts/malgun.ttf'  # Windows 기본 한글 폰트
        
        try:
            if os.path.exists(korean_font_path):
                # 폰트 파일이 존재할 경우 등록
                font_prop = fm.FontProperties(fname=korean_font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
                logging.info(f"Chart font loaded from file: {korean_font_path}")
            else:
                raise FileNotFoundError("Font file not found")
        except Exception as e:
            logging.error(f"Chart font loading failed: {e}")
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
        self.analyzer = PaperAnalyzer()
    
    def generate_performance_chart(self, paper_data, output_path):
        logging.info(f"ERROR 레벨: Generating 9:16 chart for {paper_data.get('title', 'Unknown')}")
        
        # 9:16 세로형 쇼츠 최적화 (1080x1920)
        fig, ax = plt.subplots(figsize=(6, 10.67))  # 9:16 비율
        fig.patch.set_facecolor('#000000')  # 완전한 검은색 배경
        ax.set_facecolor('#000000')
        
        # 실제 논문에서 성능 데이터 추출 (필수)
        perf_data = self.analyzer.extract_performance_data(paper_data)
        
        if not perf_data or not perf_data.get('has_valid_data'):
            raise ValueError(f"ERROR: No performance data found in paper {paper_data.get('arxiv_id', 'Unknown')}")
            
        baseline = perf_data['baseline_performance']
        proposed = perf_data['proposed_performance']
        metric = perf_data['metric_name']
        
        if baseline is None or proposed is None:
            raise ValueError(f"ERROR: Invalid performance values - baseline: {baseline}, proposed: {proposed}")
            
        values = [baseline, proposed]
        methods = ['기존\\n방법', '제안\\n방법']
        
        # 양산형 쇼츠용 시각적 개선
        colors = ['#FF3366', '#00FF88']  # 고대비 네온 컬러
        bars = ax.bar(methods, values, color=colors, alpha=0.9, width=0.5, 
                     edgecolor='white', linewidth=3)
        
        # 세로형 최적화: 상단에 제목 배치 
        ax.set_title(f'{metric} 성능 비교', color='white', fontsize=32, 
                    weight='bold', pad=40, y=0.95)
        
        # 모바일 친화적 폰트 크기
        ax.set_ylabel('성능 (%)', color='white', fontsize=28, weight='bold')
        ax.tick_params(colors='white', labelsize=24, width=2)
        
        # 테두리 제거 (쇼츠 스타일)
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # 값 표시 - 더 크고 명확하게
        improvement = ((proposed - baseline) / baseline) * 100
        for i, (bar, value) in enumerate(zip(bars, values)):
            # 바 위에 값 표시
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values) * 0.03,
                   f'{value:.1f}%', ha='center', va='bottom', 
                   color='white', fontsize=26, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.8))
            
            # 개선율 표시 (두 번째 바에만)
            if i == 1 and improvement > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                       f'+{improvement:.1f}%\\n향상', ha='center', va='center',
                       color='black', fontsize=20, weight='bold')
        
        # 격자 제거 (깔끔한 쇼츠 스타일)
        ax.grid(False)
        ax.set_ylim(0, max(values) * 1.15)
        
        # 여백 최적화 (세로형)
        plt.tight_layout()
        plt.subplots_adjust(top=0.9, bottom=0.1)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor='#000000', edgecolor='none')
        plt.close()
        
        logging.info(f"Generated 9:16 chart: {output_path} ({baseline}% → {proposed}%, +{improvement:.1f}%)")
        return output_path
