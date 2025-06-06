import edge_tts
import asyncio
import os
import logging

class TTSEngine:
    def __init__(self, voice=None):
# 환경변수에서 음성 설정 읽기 (기본값 제공)
        self.voice = voice or os.getenv('TTS_VOICE', 'ko-KR-SunHiNeural')
        
        # 양산형 쇼츠 최적화 음성들
        self.shorts_voices = {
            'korean_female': 'ko-KR-SunHiNeural',
            'korean_male': 'ko-KR-InJoonNeural', 
            'english_female': 'en-US-AriaNeural',
            'english_male': 'en-US-GuyNeural'
        }
        
        # 설정된 음성이 유효한지 확인
        if self.voice not in self.shorts_voices.values():
            logging.warning(f"Using non-optimized voice: {self.voice}")
        
        logging.info(f"TTS Engine initialized with voice: {self.voice}")
        
    async def generate_speech(self, text, output_path):
        if not text or not text.strip():
            raise ValueError("ERROR: Empty text provided for TTS generation")
            
        try:
            # 쇼츠 최적화 음성 설정
            communicate = edge_tts.Communicate(
                text, 
                self.voice,
                rate='+10%',  # 쇼츠용 약간 빠른 속도
                volume='+0%'
            )
            
            await communicate.save(output_path)
            
            # 생성된 파일 검증
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"ERROR: TTS output file not created: {output_path}")
                
            file_size = os.path.getsize(output_path)
            if file_size < 1000:  # 1KB 미만이면 에러
                raise ValueError(f"ERROR: TTS output too small ({file_size} bytes)")
            
            logging.info(f"TTS generated: {output_path} ({file_size} bytes)")
            return output_path
            
        except Exception as e:
            # TTS 에러 즉시 전파
            raise Exception(f"ERROR: TTS generation failed for text '{text[:50]}...': {e}")
            
    def generate(self, text, output_path):
        try:
            # asyncio 이벤트 루프 처리 개선
            try:
                # 기존 루프가 있는지 확인
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # 루프가 없으면 새로 만들어 실행
                return asyncio.run(self.generate_speech(text, output_path))
            
            # 루프가 이미 실행 중이면 ThreadPoolExecutor 사용
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self.generate_speech(text, output_path))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30초 타임아웃
                
        except Exception as e:
            raise Exception(f"ERROR: TTS generation failed: {e}")
            
    def estimate_duration(self, text):
        """텍스트 기반 음성 길이 추정 (쇼츠 타이밍 계산용)"""
        # 한국어: 분당 약 200자, 영어: 분당 약 150단어
        if any(ord(char) > 127 for char in text):  # 한국어 포함
            chars_per_second = 200 / 60
            return len(text) / chars_per_second
        else:  # 영어
            words = len(text.split())
            words_per_second = 150 / 60
            return words / words_per_second
