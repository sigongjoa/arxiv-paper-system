from .tts_engine import TTSEngine
from ..utils import FilenameSanitizer
import os
import logging
import time
import uuid

class Narrator:
    def __init__(self):
        self.tts = TTSEngine()
        
    def generate_narration(self, script_data):
        logging.info(f"ERROR 레벨: Generating unique narration for {script_data.get('paper_id', 'unknown')}")
        
        if not script_data or not script_data.get('scenes'):
            raise ValueError("ERROR: No scenes provided for narration generation")
            
        audio_files = []
        paper_title = script_data.get('paper_title', 'Unknown Paper')
        arxiv_id = script_data.get('paper_id', script_data.get('arxiv_id', 'unknown'))
        timestamp = int(time.time())
        
        # 절대 경로 생성
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        for i, scene in enumerate(script_data['scenes']):
            text = scene.get('text', '')
            if not text.strip():
                raise ValueError(f"ERROR: Empty text for scene {i}")
            
            # 논문 제목 기반 고유 파일명 생성
            unique_id = str(uuid.uuid4())[:8]
            sanitized_title = FilenameSanitizer.sanitize_title(paper_title, 30)
            safe_arxiv_id = arxiv_id.replace('.', '_').replace('v', '_')
            filename = f"{sanitized_title}_{safe_arxiv_id}_{timestamp}_{i}_{unique_id}.wav"
            output_path = os.path.join(project_root, "output", "audio", filename)
            
            # 디렉토리 생성 보장
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            try:
                audio_file = self.tts.generate(text, output_path)
                
                # 파일 생성 검증
                if not os.path.exists(audio_file):
                    raise FileNotFoundError(f"ERROR: Audio file not created: {audio_file}")
                    
                file_size = os.path.getsize(audio_file)
                if file_size < 1000:  # 1KB 미만
                    raise ValueError(f"ERROR: Audio file too small ({file_size} bytes): {audio_file}")
                
                audio_files.append({
                    'file': audio_file,
                    'duration': scene['duration'],
                    'scene_id': i,
                    'text': text[:50] + "..." if len(text) > 50 else text
                })
                
                logging.info(f"Generated unique audio {i}: {filename} ({file_size} bytes)")
                
            except Exception as e:
                raise Exception(f"ERROR: Audio generation failed for scene {i}: {e}")
                
        logging.info(f"Created {len(audio_files)} unique audio files for {sanitized_title}_{safe_arxiv_id}")
        return audio_files
