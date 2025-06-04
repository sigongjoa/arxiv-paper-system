from .video_renderer import VideoRenderer
from ..utils import FilenameSanitizer
import logging
import os
import time

class Composer:
    def __init__(self):
        self.renderer = VideoRenderer()
        
    def compose_video(self, visuals, audio_files, script_data):
        logging.info(f"ERROR 레벨: Composing video with {len(visuals)} visuals and {len(audio_files)} audio files")
        
        if not visuals or not audio_files:
            raise ValueError("ERROR: No visuals or audio files provided for composition")
            
        # 논문 제목과 arxiv_id로 파일명 생성
        paper_title = script_data.get('paper_title', 'Unknown Paper')
        arxiv_id = script_data.get('paper_id', script_data.get('arxiv_id', 'unknown'))
        
        filename = FilenameSanitizer.create_unique_filename(paper_title, arxiv_id, 'mp4')
        
        # 절대 경로 생성
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        output_path = os.path.join(project_root, "output", "videos", filename)
        
        # 디렉토리 생성 보장
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        video_path = self.renderer.render(visuals, audio_files, output_path)
        
        # 파일 생성 검증
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"ERROR: Video file not created at {video_path}")
            
        file_size = os.path.getsize(video_path)
        if file_size < 1000000:  # 1MB 미만
            raise ValueError(f"ERROR: Video file too small ({file_size} bytes) - composition may have failed")
        
        logging.info(f"UNIQUE video composed: {filename} ({file_size/1000000:.1f}MB)")
        return [video_path]
