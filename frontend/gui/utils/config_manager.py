import os
import json
from dotenv import load_dotenv, set_key

class ConfigManager:
    def __init__(self):
        self.env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '.env'
        )
        self.config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'config.json'
        )
        
        # .env 파일이 없으면 .env.example을 복사
        if not os.path.exists(self.env_file):
            example_file = self.env_file + '.example'
            if os.path.exists(example_file):
                with open(example_file, 'r') as src:
                    with open(self.env_file, 'w') as dst:
                        dst.write(src.read())
        
        # 환경 변수 로드
        load_dotenv(self.env_file)
        
        # 설정 파일 로드
        self.config = self.load_config()
        
    def load_config(self):
        """설정 파일 로드"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
        
    def save_config(self):
        """설정 파일 저장"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def get(self, key, default=None):
        """설정 값 가져오기"""
        # 먼저 환경 변수에서 확인
        value = os.getenv(key)
        if value:
            return value
            
        # 그 다음 설정 파일에서 확인
        return self.config.get(key, default)
        
    def set(self, key, value):
        """설정 값 저장"""
        # API 키는 .env 파일에 저장
        if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
            set_key(self.env_file, key, str(value))
        else:
            # 나머지는 config.json에 저장
            self.config[key] = value
            self.save_config()
            
    def save_all(self, settings):
        """모든 설정 저장"""
        for key, value in settings.items():
            self.set(key, value)
            
    def get_all_settings(self):
        """모든 설정 반환"""
        all_settings = {}
        
        # 환경 변수
        for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'YOUTUBE_CLIENT_ID', 
                    'YOUTUBE_CLIENT_SECRET', 'INSTAGRAM_USERNAME', 'INSTAGRAM_PASSWORD']:
            all_settings[key] = os.getenv(key, '')
            
        # 설정 파일
        all_settings.update(self.config)
        
        return all_settings
