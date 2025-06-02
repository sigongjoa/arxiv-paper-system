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
