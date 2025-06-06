"""LM Studio Client for AI Research Agents"""

import logging
import json
import time
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LMStudioConfig:
    """LM Studio 설정"""
    base_url: str = "http://localhost:1234/v1"
    api_key: str = "not-needed"
    model_name: str = "local-model"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 300

class LMStudioClient:
    """LM Studio 연결 클라이언트"""
    
    def __init__(self, config: Optional[LMStudioConfig] = None):
        self.config = config or LMStudioConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}'
        })
        logger.info(f"LM Studio client initialized: {self.config.base_url}")

    async def generate_response(self, 
                              prompt: str, 
                              system_message: str = None,
                              **kwargs) -> str:
        """텍스트 생성"""
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.config.model_name,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": False
            }
            
            start_time = time.time()
            
            response = self.session.post(
                f"{self.config.base_url}/chat/completions",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"LM Studio API 에러: {response.status_code} - {response.text}")
                raise Exception(f"LM Studio API failed: {response.status_code}")
                
            result = response.json()
            execution_time = time.time() - start_time
            
            content = result['choices'][0]['message']['content']
            usage = result.get('usage', {})
            
            logger.info(f"LLM 응답 생성 완료 - 시간: {execution_time:.2f}s, 토큰: {usage.get('total_tokens', 'unknown')}")
            
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP 요청 실패: {e}")
            raise Exception(f"LM Studio 연결 실패: {e}")
        except Exception as e:
            logger.error(f"LLM 응답 생성 실패: {e}")
            raise

    def check_connection(self) -> bool:
        """연결 상태 확인"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/models",
                timeout=10
            )
            
            if response.status_code == 200:
                models_data = response.json()
                model_count = len(models_data.get('data', []))
                logger.info(f"LM Studio 연결 확인됨. 사용 가능 모델: {model_count}")
                return True
            else:
                logger.error(f"LM Studio 연결 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"LM Studio 연결 확인 실패: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/models",
                timeout=10
            )
            
            if response.status_code == 200:
                models_data = response.json()
                return [model['id'] for model in models_data.get('data', [])]
            else:
                logger.error(f"모델 목록 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"모델 목록 조회 실패: {e}")
            return []
