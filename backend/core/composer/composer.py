from .video_renderer import VideoRenderer
import logging
import os

class Composer:
    def __init__(self):
        self.renderer = VideoRenderer()
        
    def compose_video(self, visuals, audio_files, script_data):
        try:
            # 파일명에서 특수문자 제거
            paper_id = script_data.get('paper_id', 'unknown')
            safe_paper_id = paper_id.replace('.', '_').replace('v', '_')
            
            output_path = f"output/videos/arxiv_short_{safe_paper_id}.mp4"
            
            # 디렉토리 생성 보장
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            video_path = self.renderer.render(visuals, audio_files, output_path)
            
            logging.info(f"Video composed successfully: {video_path}")
            return [video_path]
            
        except Exception as e:
            logging.error(f"Video composition error: {e}")
            raise
