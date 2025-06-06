from .title_card_generator import TitleCardGenerator
from .chart_generator import ChartGenerator
from ..utils import FilenameSanitizer
import logging
import os
import time
import uuid

class Visualizer:
    def __init__(self):
        self.title_generator = TitleCardGenerator()
        self.chart_generator = ChartGenerator()
        
    def create_visuals(self, paper_data, script_data):
        logging.info(f"ERROR 레벨: Creating unique visuals for {paper_data.get('arxiv_id')}")
        
        if not script_data or not script_data.get('scenes'):
            raise ValueError("ERROR: No scenes provided for visual generation")
        
        visuals = []
        paper_title = script_data.get('paper_title', paper_data.get('title', 'Unknown Paper'))
        arxiv_id = paper_data.get('arxiv_id', 'unknown')
        timestamp = int(time.time())
        
        # 절대 경로 생성
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        for i, scene in enumerate(script_data['scenes']):
            visual_type = scene.get('visual', 'title_card')
            
            # 논문 제목 기반 고유 파일명 생성
            unique_id = str(uuid.uuid4())[:8]
            sanitized_title = FilenameSanitizer.sanitize_title(paper_title, 30)
            safe_arxiv_id = arxiv_id.replace('.', '_').replace('v', '_')
            filename = f"{sanitized_title}_{safe_arxiv_id}_{timestamp}_{i}_{unique_id}.png"
            output_path = os.path.join(project_root, "output", "visuals", filename)
            
            # 디렉토리 생성 보장
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            try:
                if visual_type in ['hook_card', 'title_card', 'problem_visual', 'impact_visual', 'conclusion']:
                    visual_file = self.title_generator.generate(
                        paper_data['title'][:50] + "...",
                        scene['text'],
                        output_path
                    )
                elif visual_type in ['chart', 'solution_chart', 'performance_chart']:
                    try:
                        visual_file = self.chart_generator.generate_performance_chart(
                            paper_data,
                            output_path
                        )
                    except Exception as chart_error:
                        logging.error(f"Chart generation failed, using title card: {chart_error}")
                        visual_file = self.title_generator.generate(
                            paper_data['title'][:50] + "...",
                            scene['text'],
                            output_path
                        )
                elif visual_type == 'diagram':
                    # 다이어그램 타입도 차트로 처리
                    visual_file = self.chart_generator.generate_performance_chart(
                        paper_data,
                        output_path
                    )
                else:
                    # 알 수 없는 타입은 에러 (fallback 없음)
                    raise ValueError(f"ERROR: Unknown visual type '{visual_type}' for scene {i}")
                
                # 파일 생성 검증
                if not os.path.exists(visual_file):
                    raise FileNotFoundError(f"ERROR: Visual file not created: {visual_file}")
                    
                file_size = os.path.getsize(visual_file)
                if file_size < 1000:  # 1KB 미만
                    raise ValueError(f"ERROR: Visual file too small ({file_size} bytes): {visual_file}")
                
                visuals.append({
                    'file': visual_file,
                    'duration': scene['duration'],
                    'scene_id': i,
                    'type': visual_type
                })
                
                logging.info(f"Generated unique visual {i}: {filename} ({file_size} bytes)")
                
            except Exception as e:
                raise Exception(f"ERROR: Visual generation failed for scene {i} (type: {visual_type}): {e}")
                
        logging.info(f"Created {len(visuals)} unique visuals for {sanitized_title}_{safe_arxiv_id}")
        return visuals
