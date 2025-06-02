from .tts_engine import TTSEngine
import os
import logging

class Narrator:
    def __init__(self):
        self.tts = TTSEngine()
        
    def generate_narration(self, script_data):
        audio_files = []
        
        try:
            for i, scene in enumerate(script_data['scenes']):
                output_path = f"output/audio/scene_{i}.wav"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                audio_file = self.tts.generate(scene['text'], output_path)
                audio_files.append({
                    'file': audio_file,
                    'duration': scene['duration'],
                    'scene_id': i
                })
                
            return audio_files
            
        except Exception as e:
            logging.error(f"Narration error: {e}")
            raise
