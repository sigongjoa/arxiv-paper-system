import sys
import os
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

try:
    import pillow_compat
except ImportError:
    pass

from moviepy.editor import *
import os
import logging

class VideoRenderer:
    def render(self, visuals, audio_files, output_path):
        logging.info(f"ERROR 레벨: Rendering 9:16 shorts video with {len(visuals)} scenes")
        
        if not visuals or not audio_files:
            raise ValueError("ERROR: No visuals or audio files provided for rendering")
            
        if len(visuals) != len(audio_files):
            raise ValueError(f"ERROR: Mismatched visuals ({len(visuals)}) and audio ({len(audio_files)}) count")
        
        clips = []
        total_duration = 0
        
        for i, (visual, audio) in enumerate(zip(visuals, audio_files)):
            if not os.path.exists(visual['file']):
                raise FileNotFoundError(f"ERROR: Visual file not found: {visual['file']}")
                
            if not os.path.exists(audio['file']):
                raise FileNotFoundError(f"ERROR: Audio file not found: {audio['file']}")
            
            # 이미지 클립 생성 - 9:16 세로형 쇼츠 최적화
            img_clip = ImageClip(visual['file']).set_duration(visual['duration'])
            
            # 정확한 9:16 비율 (1080x1920) 강제 적용
            target_width, target_height = 1080, 1920
            
            # 이미지를 1920 높이에 맞추고 너비 조정
            img_clip = img_clip.resize(height=target_height)
            
            # 너비가 1080보다 클 경우 중앙 크롭
            if img_clip.w > target_width:
                img_clip = img_clip.crop(x_center=img_clip.w/2, width=target_width)
            # 너비가 부족하면 검은색 패딩으로 채움
            elif img_clip.w < target_width:
                img_clip = img_clip.on_color(size=(target_width, target_height), color=(0,0,0))
            
            # 오디오 클립 로드 및 동기화
            audio_clip = AudioFileClip(audio['file'])
            
            # 영상과 오디오 길이 동기화
            audio_duration = audio_clip.duration
            visual_duration = visual['duration']
            
            # 오디오 길이에 맞춰 비주얼 길이 자동 조정
            sync_duration = audio_duration
            visual['duration'] = sync_duration  # visual duration 업데이트
            
            img_clip = img_clip.set_duration(sync_duration)
            audio_clip = audio_clip.set_duration(sync_duration)
            
            img_clip = img_clip.set_audio(audio_clip)
            clips.append(img_clip)
            total_duration += sync_duration
            
            logging.info(f"Scene {i}: {sync_duration:.2f}s ({visual['file']})")
        
        # 60초 제한 엄격 검증
        if total_duration > 60.5:  # 0.5초 여유
            raise ValueError(f"ERROR: Total video duration {total_duration:.2f}s exceeds 60s limit")
        
        if total_duration < 15:  # 15초 미만이면 에러
            raise ValueError(f"ERROR: Total video duration {total_duration:.2f}s too short (minimum 15s)")
        
        # 클립들 연결
        final_video = concatenate_videoclips(clips)
        
        # 9:16 비율 최종 확인
        if final_video.w != 1080 or final_video.h != 1920:
            raise ValueError(f"ERROR: Final video resolution {final_video.w}x{final_video.h} is not 1080x1920")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 양산형 쇼츠 최적화 인코딩 설정
        try:
            final_video.write_videofile(
                output_path,
                fps=30,  # 쇼츠 표준 프레임레이트
                codec='libx264',
                audio_codec='aac',
                bitrate='8000k',  # 고품질 비트레이트
                audio_bitrate='192k',
                preset='medium',  # 품질-속도 균형
                ffmpeg_params=[
                    '-profile:v', 'high',
                    '-level', '4.2',
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart'  # 스트리밍 최적화
                ],
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None  # moviepy 로거 비활성화
            )
        except Exception as e:
            raise Exception(f"ERROR: Video encoding failed: {e}")
        
        # 메모리 정리
        try:
            final_video.close()
            for clip in clips:
                clip.close()
        except Exception as e:
            logging.warning(f"Memory cleanup warning: {e}")
        
        # 최종 파일 검증
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"ERROR: Failed to create output video: {output_path}")
            
        file_size = os.path.getsize(output_path)
        if file_size < 1000000:  # 1MB 미만이면 에러
            raise ValueError(f"ERROR: Output video too small ({file_size} bytes), encoding failed")
        
        logging.info(f"9:16 shorts video rendered: {output_path} ({total_duration:.2f}s, {file_size/1000000:.1f}MB)")
        return output_path
