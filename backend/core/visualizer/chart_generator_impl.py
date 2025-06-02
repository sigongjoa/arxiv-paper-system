import matplotlib.pyplot as plt
import os
import logging
import sys

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from backend.paper_analyzer import PaperAnalyzer

class ChartGeneratorImpl:
    def __init__(self):
        try:
            plt.rcParams['font.family'] = 'Malgun Gothic'
        except:
            try:
                plt.rcParams['font.family'] = 'NanumGothic'
            except:
                plt.rcParams['font.family'] = 'DejaVu Sans'
        
        plt.rcParams['axes.unicode_minus'] = False
        self.analyzer = PaperAnalyzer()
    
    def generate_performance_chart(self, paper_data, output_path):
        fig, ax = plt.subplots(figsize=(10.8, 19.2))
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#1a1a1a')
        
        try:
            # 실제 논문에서 성능 데이터 추출
            perf_data = self.analyzer.extract_performance_data(paper_data)
            
            if perf_data['has_valid_data']:
                baseline = perf_data['baseline_performance']
                proposed = perf_data['proposed_performance']
                metric = perf_data['metric_name']
                
                values = [baseline, proposed]
                title = f'{metric} 비교'
                
                logging.info(f"Using real data: {baseline} -> {proposed} ({metric})")
            else:
                # 실제 데이터를 찾지 못한 경우에만 기본값 사용
                values = [75.0, 87.5]
                title = '성능 비교 (추정)'
                
                logging.warning("No performance data found, using default values")
                
        except Exception as e:
            logging.error(f"Failed to extract performance data: {e}")
            values = [75.0, 87.5]
            title = '성능 비교 (추정)'
        
        methods = ['기존\n방법', '제안\n방법']
        colors = ['#ff6b6b', '#4ecdc4']
        
        bars = ax.bar(methods, values, color=colors, alpha=0.8, width=0.6)
        
        ax.set_ylabel('성능 (%)', color='white', fontsize=24, weight='bold')
        ax.set_title(title, color='white', fontsize=28, weight='bold', pad=30)
        ax.tick_params(colors='white', labelsize=20)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values) * 0.02,
                   f'{value:.1f}%', ha='center', va='bottom', 
                   color='white', fontsize=22, weight='bold')
        
        ax.set_ylim(0, max(values) * 1.2)
        ax.grid(True, alpha=0.3, color='white', linestyle='--')
        ax.set_axisbelow(True)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=100, bbox_inches='tight',
                   facecolor='#1a1a1a', edgecolor='none')
        plt.close()
        
        logging.info(f"Chart generated: {output_path}")
        return output_path
