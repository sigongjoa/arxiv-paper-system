from .summarizer import Summarizer
from .visualizer import Visualizer
from .narrator import Narrator
from .composer import Composer
from .publisher import Publisher
import logging

class Pipeline:
    def __init__(self):
        self.summarizer = Summarizer()
        self.visualizer = Visualizer()
        self.narrator = Narrator()
        self.composer = Composer()
        self.publisher = Publisher()
    
    def process_paper(self, arxiv_id, paper_data):
        try:
            logging.info(f"Starting video pipeline for paper: {paper_data.get('title', 'Unknown')}")
            
            # 스크립트 생성
            logging.info("Step 1/5: Generating script...")
            script = self.summarizer.generate_script(paper_data)
            logging.info(f"Script generated with {len(script.get('scenes', []))} scenes")
            
            # 시각 자료 생성
            logging.info("Step 2/5: Creating visual materials...")
            visuals = self.visualizer.create_visuals(paper_data, script)
            logging.info(f"Generated {len(visuals)} visual files")
            
            # 나레이션 생성
            logging.info("Step 3/5: Generating narration...")
            narration = self.narrator.generate_narration(script)
            logging.info(f"Generated narration for {len(narration)} audio segments")
            
            # 비디오 합성
            logging.info("Step 4/5: Composing video...")
            video_paths = self.composer.compose_video(visuals, narration, script)
            logging.info(f"Video composition complete: {video_paths}")
            
            # 배포
            logging.info("Step 5/5: Publishing video...")
            results = self.publisher.distribute(video_paths)
            logging.info(f"Video successfully published to: {results}")
            
            logging.info(f"Pipeline completed successfully for {arxiv_id}")
            return results
            
        except Exception as e:
            logging.error(f"Pipeline error for {arxiv_id}: {e}")
            raise
