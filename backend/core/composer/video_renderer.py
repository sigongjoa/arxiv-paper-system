# Pillow 10+ 호환성 패치 적용
import sys
import os
# 루트 디렉토리로 이동 (src/composer 에서 2단계 상위)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)
try:
    import pillow_compat  # Pillow 호환성 패치
except ImportError:
    pass

from moviepy.editor import *
import os
import logging

class VideoRenderer:
    def render(self, visuals, audio_files, output_path):
        try:
            clips = []
            
            for i, (visual, audio) in enumerate(zip(visuals, audio_files)):
                # 이미지 클립 생성 (PIL 호환성 문제 해결)
                img_clip = ImageClip(visual['file']).set_duration(visual['duration'])
                
                # 9:16 비율로 리사이즈 (PIL.Image.ANTIALIAS 문제 해결)
                img_clip = img_clip.resize(height=1920)
                
                # 너비가 1080보다 클 경우 크롭
                if img_clip.w > 1080:
                    img_clip = img_clip.crop(x_center=img_clip.w/2, width=1080)
                else:
                    # 너비가 부족하면 패딩
                    img_clip = img_clip.on_color(size=(1080, 1920), color=(0,0,0))
                
                # 오디오 클립 로드
                if os.path.exists(audio['file']):
                    try:
                        audio_clip = AudioFileClip(audio['file'])
                        img_clip = img_clip.set_audio(audio_clip)
                    except Exception as e:
                        logging.warning(f"Audio loading failed: {e}")
                
                clips.append(img_clip)
            
            if not clips:
                raise Exception("No clips generated")
            
            # 클립들 연결
            final_video = concatenate_videoclips(clips)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # 메모리 정리
            final_video.close()
            for clip in clips:
                clip.close()
            
            logging.info(f"Video rendered: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Video rendering error: {e}")
            raise
