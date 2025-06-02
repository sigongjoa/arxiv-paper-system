import edge_tts
import asyncio
import os
import logging

class TTSEngine:
    def __init__(self):
        self.voice = "ko-KR-SunHiNeural"
        
    async def generate_speech(self, text, output_path):
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            logging.info(f"TTS generated: {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"TTS error: {e}")
            raise
            
    def generate(self, text, output_path):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 이벤트 루프가 실행 중일 때
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, text, output_path)
                    return future.result()
            else:
                # 이벤트 루프가 없을 때
                return asyncio.run(self.generate_speech(text, output_path))
        except RuntimeError:
            # 이벤트 루프가 없는 경우
            return asyncio.run(self.generate_speech(text, output_path))
    
    def _run_in_new_loop(self, text, output_path):
        """새로운 이벤트 루프에서 실행"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.generate_speech(text, output_path))
        finally:
            loop.close()
