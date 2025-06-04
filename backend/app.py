import sys
import os

# 프로젝트 루트 설정
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Pillow 10+ 호환성 패치
try:
    from backend import pillow_compat
except ImportError:
    pass

from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import logging
import requests
import json
import uuid
import threading
from datetime import datetime
from backend.processor import PaperProcessor
from backend.core.pipeline import Pipeline
from backend.log_stream import setup_log_capture, log_capture
from backend.core.publisher.youtube_metadata import YouTubeMetadata
from backend.core.publisher.youtube_auth_web import YouTubeAuthWeb

# Flask 앱 설정 - frontend 폴더를 template/static으로 사용
template_dir = os.path.join(project_root, 'frontend', 'templates')
static_dir = os.path.join(project_root, 'frontend', 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
logging.basicConfig(level=logging.INFO)
setup_log_capture()
processor = PaperProcessor()
pipeline = Pipeline()

# 업로드 상태 추적을 위한 메모리 저장소
upload_status = {}

def check_lm_studio():
    """LM Studio 서버 연결 상태 확인"""
    try:
        response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/lm-studio/status')
def lm_studio_status():
    """LM Studio 연결 상태 확인 API"""
    is_connected = check_lm_studio()
    return jsonify({
        'connected': is_connected,
        'url': 'http://127.0.0.1:1234',
        'message': 'LM Studio 연결 성공' if is_connected else 'LM Studio 연결 실패 - 모델 로드 확인 필요'
    })

@app.route('/api/process', methods=['POST'])
def process_paper():
    arxiv_id = None
    try:
        # LM Studio 연결 상태 확인 (필수)
        if not check_lm_studio():
            raise Exception('LM Studio 서버에 연결할 수 없습니다. 모델을 로드하고 다시 시도하세요.')
        
        data = request.get_json()
        if not data or not data.get('arxiv_id'):
            raise ValueError('arxiv_id 필수')
            
        arxiv_id = data.get('arxiv_id')
        
        # 논문 데이터 가져오기
        logging.info(f"ERROR 레벨: Starting mass-production processing for {arxiv_id}")
        paper_result = processor.process_arxiv_paper(arxiv_id)
        
        # 비디오 생성 파이프라인 실행
        video_result = pipeline.process_paper(arxiv_id, paper_result['paper'])
        
        # 비디오 파일 생성 확인
        if not video_result.get('video_paths') or not video_result['video_paths']:
            raise Exception('비디오 파일이 생성되지 않았습니다.')
            
        # 생성된 비디오 파일 존재 확인
        for video_path in video_result['video_paths']:
            if not os.path.exists(video_path):
                raise Exception(f'비디오 파일이 생성되지 않았습니다: {video_path}')
        
        logging.info(f"Mass-production complete for {arxiv_id}: {video_result.get('video_paths')}")
        
        return jsonify({
            'paper': paper_result['paper'],
            'summary': paper_result['summary'],
            'videos': video_result,
            'status': 'completed',
            'processing_time': video_result.get('processing_time', 0)
        })
        
    except Exception as e:
        error_msg = f"ERROR: Mass-production failed for {arxiv_id or 'unknown'}: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            'error': error_msg,
            'status': 'error',
            'arxiv_id': arxiv_id
        }), 500

@app.route('/api/publish', methods=['POST'])
def publish_video():
    """비디오 업로드 API"""
    try:
        data = request.get_json()
        
        # 업로드 ID 생성
        upload_id = str(uuid.uuid4())
        
        # 업로드 상태 초기화
        upload_status[upload_id] = {
            'completed': False,
            'platforms': {},
            'started_at': datetime.now().isoformat()
        }
        
        for platform in data['platforms']:
            upload_status[upload_id]['platforms'][platform] = {
                'progress': 0,
                'status': 'queued',
                'success': False
            }
        
        # 백그라운드에서 업로드 실행
        upload_thread = threading.Thread(
            target=perform_upload,
            args=(upload_id, data)
        )
        upload_thread.daemon = True
        upload_thread.start()
        
        return jsonify({
            'upload_id': upload_id,
            'status': 'started',
            'platforms': data['platforms']
        })
        
    except Exception as e:
        logging.error(f"Publish error: {e}")
        return jsonify({'error': str(e)}), 500

def perform_upload(upload_id, data):
    """백그라운드에서 실제 업로드 수행"""
    try:
        video_path = data.get('video_path', '').replace('/output/', 'output/')
        if not video_path.startswith('output/'):
            # URL에서 파일 경로 추출
            video_select = data.get('video_url', '')
            if '/output/videos/' in video_select:
                filename = video_select.split('/output/videos/')[-1]
                video_path = os.path.join(project_root, 'output', 'videos', filename)
        else:
            video_path = os.path.join(project_root, video_path)
        
        logging.info(f"Starting upload for {upload_id}: {video_path}")
        
        for platform in data['platforms']:
            platform_status = upload_status[upload_id]['platforms'][platform]
            platform_status['status'] = 'uploading'
            platform_status['progress'] = 10
            
            try:
                if platform == 'youtube':
                    result = upload_to_youtube(video_path, data)
                    platform_status['success'] = result['status'] == 'success'
                    platform_status['progress'] = 100
                    platform_status['status'] = 'completed' if result['status'] == 'success' else 'failed'
                    platform_status['message'] = result.get('message', '')
                    if 'video_id' in result:
                        platform_status['video_id'] = result['video_id']
                        platform_status['url'] = result.get('url', '')
                else:
                    # 다른 플랫폼은 아직 구현되지 않음
                    platform_status['success'] = False
                    platform_status['progress'] = 0
                    platform_status['status'] = 'not_implemented'
                    platform_status['message'] = f'{platform} upload not implemented yet'
                    
            except Exception as e:
                logging.error(f"Upload failed for {platform}: {e}")
                platform_status['success'] = False
                platform_status['progress'] = 0
                platform_status['status'] = 'failed'
                platform_status['message'] = str(e)
        
        upload_status[upload_id]['completed'] = True
        upload_status[upload_id]['completed_at'] = datetime.now().isoformat()
        
        logging.info(f"Upload {upload_id} completed")
        
    except Exception as e:
        logging.error(f"Upload thread error: {e}")
        upload_status[upload_id]['completed'] = True
        upload_status[upload_id]['error'] = str(e)

def upload_to_youtube(video_path, data):
    """YouTube 업로드 실행"""
    try:
        auth = YouTubeAuthWeb()
        if not auth.is_authenticated():
            return {'status': 'error', 'message': 'YouTube authentication required'}
        
        service = auth.get_authenticated_service()
        if not service:
            return {'status': 'error', 'message': 'Failed to get YouTube service'}
        
        from backend.core.publisher.youtube_metadata import YouTubeMetadata
        from googleapiclient.http import MediaFileUpload
        
        metadata_gen = YouTubeMetadata()
        metadata = metadata_gen.create_metadata(
            title=data.get('title'),
            description=data.get('description'),
            tags=data.get('tags', '').split() if data.get('tags') else None
        )
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = service.videos().insert(
            part=','.join(metadata.keys()),
            body=metadata,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Upload progress: {int(status.progress() * 100)}%")
        
        if 'id' in response:
            video_id = response['id']
            return {
                'status': 'success',
                'video_id': video_id,
                'url': f'https://youtube.com/watch?v={video_id}'
            }
        else:
            return {'status': 'error', 'message': f'Upload failed: {response}'}
            
    except Exception as e:
        logging.error(f"YouTube upload error: {e}")
        return {'status': 'error', 'message': str(e)}

@app.route('/api/upload/status/<upload_id>')
def get_upload_status(upload_id):
    """업로드 상태 조회 API"""
    if upload_id not in upload_status:
        return jsonify({'error': 'Upload ID not found'}), 404
    
    return jsonify(upload_status[upload_id])

@app.route('/api/youtube/auth')
def youtube_auth():
    """YouTube 인증 시작"""
    try:
        auth = YouTubeAuthWeb()
        auth_url = auth.get_auth_url()
        return jsonify({'auth_url': auth_url})
    except Exception as e:
        logging.error(f"YouTube auth error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/youtube/callback')
def youtube_callback():
    """YouTube OAuth 콜백"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            return jsonify({'error': 'Authorization code missing'}), 400
        
        auth = YouTubeAuthWeb()
        auth.handle_callback(code, state)
        
        return render_template('oauth_success.html')
    except Exception as e:
        logging.error(f"YouTube callback error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/youtube/status')
def youtube_status():
    """YouTube 인증 상태 확인"""
    try:
        auth = YouTubeAuthWeb()
        is_authenticated = auth.is_authenticated()
        return jsonify({'authenticated': is_authenticated})
    except Exception as e:
        logging.error(f"YouTube status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/settings', methods=['GET', 'POST'])
def pipeline_settings():
    if request.method == 'GET':
        return jsonify({
            'tts_voice': 'ko-KR-SunHiNeural',
            'video_resolution': '1080x1920',
            'script_style': 'engaging',
            'visual_theme': 'dark'
        })
    
    try:
        settings = request.get_json()
        # TODO: 설정 저장 로직
        return jsonify({'status': 'saved'})
    except Exception as e:
        logging.error(f"Settings error: {e}")
        raise

@app.route('/api/pipeline/status/<arxiv_id>')
def pipeline_status(arxiv_id):
    # TODO: 실시간 진행상황 조회
    return jsonify({
        'steps': [
            {'name': 'script', 'status': 'completed'},
            {'name': 'visuals', 'status': 'processing'},
            {'name': 'audio', 'status': 'pending'},
            {'name': 'video', 'status': 'pending'}
        ],
        'progress': 25
    })

# 정적 파일 서빙 - output 폴더
@app.route('/output/<path:filename>')
def serve_output_file(filename):
    output_dir = os.path.join(project_root, 'output')
    return send_from_directory(output_dir, filename)

# 비디오 파일 직접 서빙
@app.route('/api/video/<arxiv_id>')
def get_video(arxiv_id):
    try:
        video_dir = os.path.join(project_root, 'output', 'videos')
        
        if not os.path.exists(video_dir):
            return jsonify({'error': 'Video directory not found', 'path': video_dir}), 404
        
        # arxiv_id로 생성된 비디오 파일 찾기
        files = os.listdir(video_dir)
        logging.info(f"Looking for video with ID '{arxiv_id}' in {video_dir}: {files}")
        
        # 논문 제목 기반 파일명 매칭
        for filename in files:
            if filename.endswith('.mp4'):
                logging.info(f"Checking file: {filename}")
                # arxiv_id가 파일명에 포함되어 있는지 확인
                clean_arxiv_id = arxiv_id.replace('.', '_').replace('v', '_')
                if clean_arxiv_id in filename or arxiv_id in filename:
                    video_url = f'/output/videos/{filename}'
                    file_path = os.path.join(video_dir, filename)
                    file_size = os.path.getsize(file_path)
                    logging.info(f"✓ Found video: {filename}")
                    return jsonify({
                        'video_url': video_url, 
                        'filename': filename,
                        'size': file_size
                    })
        
        # 정확한 매칭만 허용 - 비디오 없으면 404 반환
        return jsonify({'error': f"No video found for {arxiv_id}. Available files: {files}"}), 404
        
    except Exception as e:
        logging.error(f"ERROR 레벨: Video fetch error: {e}")
        return jsonify({'error': str(e)}), 500

# 디버깅을 위한 파일 목록 조회
@app.route('/api/debug/files')
def debug_files():
    try:
        result = {}
        
        # output 디렉토리 구조 조회
        for subdir in ['videos', 'audio', 'visuals']:
            dir_path = os.path.join(project_root, 'output', subdir)
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                file_details = []
                for f in files:
                    file_path = os.path.join(dir_path, f)
                    if os.path.isfile(file_path):
                        file_details.append({
                            'name': f,
                            'size': os.path.getsize(file_path),
                            'created': os.path.getctime(file_path)
                        })
                result[subdir] = {
                    'count': len(file_details),
                    'files': file_details
                }
            else:
                result[subdir] = 'Directory not found'
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 진단 및 빠른 테스트 API
@app.route('/api/quick-test', methods=['POST'])
def quick_test():
    """단순 논문 데이터 가져오기 테스트"""
    try:
        data = request.get_json() or {}
        arxiv_id = data.get('arxiv_id', '2301.07041')
        
        # 단순히 processor만 테스트
        logging.info(f"Quick test for {arxiv_id}")
        paper_result = processor.process_arxiv_paper(arxiv_id)
        
        return jsonify({
            'status': 'success',
            'paper': paper_result['paper'],
            'message': 'arXiv API 연결 성공 - 논문 데이터 가져오기 완료'
        })
        
    except Exception as e:
        logging.error(f"Quick test error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'arXiv API 연결 문제 또는 네트워크 오류'
        }), 500

# TTS 테스트 API
@app.route('/api/test/create_video', methods=['POST'])
def test_create_video():
    """간단한 TTS 테스트"""
    try:
        data = request.get_json() or {}
        test_text = data.get('text', '안녕하세요. 테스트 음성입니다.')
        
        # TTS 테스트
        from backend.core.narrator.tts_engine import TTSEngine
        import time
        
        tts = TTSEngine()
        timestamp = int(time.time())
        audio_path = os.path.join(project_root, 'output', 'audio', f'test_{timestamp}.wav')
        
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        audio_file = tts.generate(test_text, audio_path)
        
        if os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            return jsonify({
                'status': 'success',
                'audio_file': audio_file,
                'size': file_size,
                'message': 'TTS 테스트 성공'
            })
        else:
            return jsonify({'status': 'failed', 'message': 'Audio file not created'}), 500
            
    except Exception as e:
        logging.error(f"TTS test error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

# 시스템 상태 체크 API
@app.route('/api/system/status')
def system_status():
    """시스템 전반 상태 체크"""
    try:
        status = {
            'lm_studio': check_lm_studio(),
            'directories': {},
            'dependencies': {}
        }
        
        # 디렉토리 체크
        for subdir in ['videos', 'audio', 'visuals']:
            dir_path = os.path.join(project_root, 'output', subdir)
            status['directories'][subdir] = os.path.exists(dir_path)
        
        # 의존성 체크
        try:
            import edge_tts
            status['dependencies']['edge_tts'] = True
        except ImportError:
            status['dependencies']['edge_tts'] = False
            
        try:
            import moviepy
            status['dependencies']['moviepy'] = True
        except ImportError:
            status['dependencies']['moviepy'] = False
            
        try:
            import matplotlib
            status['dependencies']['matplotlib'] = True
        except ImportError:
            status['dependencies']['matplotlib'] = False
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """로그 조회 API"""
    try:
        last_n = request.args.get('last', type=int)
        logs = log_capture.get_logs(last_n)
        return jsonify({'logs': logs})
    except Exception as e:
        logging.error(f"Log fetch error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/stream')
def logs_stream():
    """실시간 로그 스트림 (SSE)"""
    def generate():
        last_count = 0
        while True:
            current_logs = log_capture.get_logs()
            if len(current_logs) > last_count:
                new_logs = current_logs[last_count:]
                for log in new_logs:
                    data = json.dumps(log)
                    yield f"data: {data}\n\n"
                last_count = len(current_logs)
            import time
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/videos')
def get_videos():
    """비디오 목록 조회 API"""
    try:
        video_dir = os.path.join(project_root, 'output', 'videos')
        
        if not os.path.exists(video_dir):
            return jsonify({'videos': []})
        
        videos = []
        for filename in os.listdir(video_dir):
            if filename.endswith('.mp4'):
                file_path = os.path.join(video_dir, filename)
                file_size = os.path.getsize(file_path)
                
                videos.append({
                    'filename': filename,
                    'url': f'/output/videos/{filename}',
                    'path': f'output/videos/{filename}',
                    'size': file_size,
                    'created': os.path.getctime(file_path)
                })
        
        # 생성 시간순 정렬 (최신순)
        videos.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({'videos': videos})
    except Exception as e:
        logging.error(f"Videos fetch error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=== arXiv to Shorts Flask App ===")
    print("LM Studio 연결 상태 확인 중...")
    
    if check_lm_studio():
        print("✓ LM Studio 연결 성공 (http://127.0.0.1:1234)")
        print("플래스크 앱 시작 중...")
    else:
        print("✗ LM Studio 연결 실패")
        print("경고: LM Studio를 실행하고 모델을 로드해주세요")
        print("앱은 시작되지만 AI 기능이 작동하지 않습니다")
    
    print("\nFlask 앱 접속: http://localhost:5000")
    print("LM Studio 상태 확인: http://localhost:5000/api/lm-studio/status")
    print("="*50)
    
    app.run(debug=True)