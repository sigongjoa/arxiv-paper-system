# Shorts-optimized configuration
# 하드코딩 제거 - 환경변수에서 읽어옴
import os

SHORTS_CONFIG = {
    "AI_MODEL": os.getenv("AI_MODEL", "gpt-4"),
    "RESOLUTION": "1080x1920",  # 9:16 세로형 고정
    "FPS": 30,
    "MAX_DURATION": 60,  # 60초 고정
    "TTS_ENGINE": "edge-tts",
    "VOICE": os.getenv("TTS_VOICE", "ko-KR-SunHiNeural"), 
    "AUTO_UPLOAD": False,
    "ADD_HASHTAGS": True,
    
    # 양산형 쇼츠 전용 설정
    "SHORTS_STYLE": os.getenv("SHORTS_STYLE", "viral"),
    "HOOK_DURATION": 3,  # 첫 3초 훅
    "MIN_DURATION": 30,  # 최소 30초
    "TEXT_MAX_LENGTH": 500,  # TTS 텍스트 길이 제한
    "BATCH_SIZE": int(os.getenv("BATCH_SIZE", "5")),  # 동시 처리 수
    
    # 품질 설정
    "VIDEO_BITRATE": "8000k",
    "AUDIO_BITRATE": "192k", 
    "TTS_RATE": "+10%",  # 쇼츠용 빠른 속도
    
    # 에러 처리
    "STRICT_MODE": os.getenv("STRICT_MODE", "true").lower() == "true",
    "ALLOW_FALLBACK": False  # fallback 완전 금지
}

def get_config():
    """환경변수 우선, 없으면 기본값 사용"""
    return SHORTS_CONFIG

def validate_shorts_config():
    """쇼츠 설정 유효성 검사"""
    config = get_config()
    
    if config["MAX_DURATION"] != 60:
        raise ValueError("ERROR: MAX_DURATION must be 60 for shorts")
        
    if config["RESOLUTION"] != "1080x1920":
        raise ValueError("ERROR: RESOLUTION must be 1080x1920 for 9:16 shorts")
        
    if config["ALLOW_FALLBACK"]:
        raise ValueError("ERROR: ALLOW_FALLBACK must be False for production")
        
    return True
