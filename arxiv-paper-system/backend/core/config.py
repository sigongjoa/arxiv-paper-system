import os

class Config:
    """Backend 서비스 설정"""
    # 데이터베이스 설정
    DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')
    DATABASE_NAME = "arxiv_papers.db"
    DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)

    # 모델 캐시 설정
    MODEL_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')

    # LM Studio 설정
    LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
    LM_STUDIO_API_KEY = "not-needed" # LM Studio는 일반적으로 API 키가 필요 없음
    LM_STUDIO_MODEL_NAME = "local-model" # 로컬에서 실행 중인 모델 이름
    LM_STUDIO_MAX_TOKENS = 2000
    LM_STUDIO_TEMPERATURE = 0.7
    LM_STUDIO_TIMEOUT = 300

    # 로깅 설정 (기본값)
    LOG_LEVEL = "INFO"
    LOG_FILE = "app.log"

    # 검색 및 추천 엔진 설정
    RECOMMENDATION_TOP_K = 10
    RESEARCH_DISCOVERY_TOP_K = 5

    def __init__(self):
        os.makedirs(self.DATABASE_DIR, exist_ok=True)
        os.makedirs(self.MODEL_CACHE_DIR, exist_ok=True)

    @classmethod
    def get_db_path(cls):
        return cls.DATABASE_PATH

    @classmethod
    def get_model_cache_dir(cls):
        return cls.MODEL_CACHE_DIR 