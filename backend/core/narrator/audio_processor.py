import os
import logging

class AudioProcessor:
    def process(self, audio_path):
        logging.warning(f"AudioProcessor.process() - Using passthrough mode")
        
        # 기본 구현 - 파일이 존재하면 그대로 반환
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # TODO: 실제 오디오 처리 구현
        # - pydub를 사용한 노이즈 제거
        # - ffmpeg를 사용한 볼륨 정규화
        # - 압축 및 포맷 변환
        
        return audio_path  # 현재는 원본 그대로 반환
