from .title_card_generator import TitleCardGenerator
from .chart_generator import ChartGenerator
import logging

class Visualizer:
    def __init__(self):
        self.title_generator = TitleCardGenerator()
        self.chart_generator = ChartGenerator()
        
    def create_visuals(self, paper_data, script_data):
        visuals = []
        
        try:
            for i, scene in enumerate(script_data['scenes']):
                visual_type = scene['visual']
                output_path = f"output/visuals/scene_{i}.png"
                
                if visual_type == 'title_card':
                    visual_file = self.title_generator.generate(
                        paper_data['title'][:50] + "...",
                        scene['text'],
                        output_path
                    )
                elif visual_type == 'chart':
                    visual_file = self.chart_generator.generate_performance_chart(
                        paper_data,
                        output_path
                    )
                else:
                    # 기본 타이틀 카드
                    visual_file = self.title_generator.generate(
                        "Research Insight",
                        scene['text'],
                        output_path
                    )
                
                visuals.append({
                    'file': visual_file,
                    'duration': scene['duration'],
                    'scene_id': i
                })
                
            return visuals
            
        except Exception as e:
            logging.error(f"Visual generation error: {e}")
            raise
