import requests
import logging
from typing import Dict, List, Optional, Union, AsyncGenerator
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class LMStudioClient:
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url
        self.models = {
            "paper_summary": {
                "name": "qwen2.5-7b-instruct",
                "context_length": 32768,
                "temperature": 0.1,
                "max_tokens": 1500
            },
            "technical_analysis": {
                "name": "llama-3.1-8b-instruct", 
                "context_length": 131072,
                "temperature": 0.05,
                "max_tokens": 2000
            },
            "realtime_chat": {
                "name": "llama-3.2-3b-instruct",
                "context_length": 8192,
                "temperature": 0.2,
                "max_tokens": 800
            },
            "math_analysis": {
                "name": "mathstral-7b",
                "context_length": 32768,
                "temperature": 0.0,
                "max_tokens": 1200
            }
        }
        
        self.optimization_config = {
            "gpu_offload_layers": 28,
            "batch_size": 512,
            "flash_attention": True,
            "parallel_requests": 4
        }
    
    async def generate_response(self, prompt: str, use_case: str = "paper_summary", stream: bool = False) -> Union[str, AsyncGenerator[str, None]]:
        """Generate response with optimized model selection"""
        try:
            model_config = self.models.get(use_case, self.models["paper_summary"])
            
            logger.info(f"Using model {model_config['name']} for {use_case}")
            
            payload = {
                "model": model_config["name"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": model_config["temperature"],
                "max_tokens": model_config["max_tokens"],
                "stream": stream
            }
            
            if stream:
                return self._stream_request(payload)
            else:
                return await self._single_request(payload)
                
        except Exception as e:
            logger.error(f"LM Studio request failed: {e}")
            raise
    
    async def generate_response_stream(self, prompt: str, use_case: str = "paper_summary") -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            model_config = self.models.get(use_case, self.models["paper_summary"])
            
            logger.info(f"Using model {model_config['name']} for {use_case} (streaming)")
            
            payload = {
                "model": model_config["name"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": model_config["temperature"],
                "max_tokens": model_config["max_tokens"],
                "stream": True
            }
            
            async for chunk in self._stream_request(payload):
                yield chunk
                
        except Exception as e:
            logger.error(f"LM Studio stream failed: {e}")
            raise
    
    async def _single_request(self, payload: Dict) -> str:
        """Send single request to LM Studio"""
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            if 'choices' not in data or not data['choices']:
                raise Exception("Invalid response format")
            
            content = data['choices'][0]['message']['content'].strip()
            return self._clean_response(content)
            
        except Exception as e:
            logger.error(f"Single request failed: {e}")
            raise
    
    async def _stream_request(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream request to LM Studio"""
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Stream request failed: {e}")
            raise
    
    def _clean_response(self, content: str) -> str:
        """Clean LLM response"""
        if content.startswith('```'):
            lines = content.split('\n')
            if lines[0].strip() in ['```json', '```']:
                content = '\n'.join(lines[1:])
            if content.endswith('```'):
                content = content[:-3]
        
        return content.strip()
    
    async def check_health(self) -> Dict:
        """Check LM Studio server health"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            response.raise_for_status()
            
            models = response.json()
            return {
                "status": "healthy",
                "available_models": [m.get("id", "unknown") for m in models.get("data", [])],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_model_performance(self) -> Dict:
        """Get performance metrics for different models"""
        performance_data = {}
        
        for use_case, config in self.models.items():
            try:
                test_prompt = "Test prompt for performance measurement"
                start_time = datetime.now()
                
                await self.generate_response(test_prompt, use_case)
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                performance_data[use_case] = {
                    "model": config["name"],
                    "response_time": response_time,
                    "context_length": config["context_length"],
                    "status": "available"
                }
                
            except Exception as e:
                performance_data[use_case] = {
                    "model": config["name"],
                    "status": "unavailable",
                    "error": str(e)
                }
        
        return performance_data
    
    def get_optimal_model(self, task_type: str, content_length: int) -> str:
        """Get optimal model based on task and content length"""
        if task_type == "mathematical" or "equation" in task_type.lower():
            return "math_analysis"
        elif content_length > 50000:
            return "technical_analysis"
        elif "chat" in task_type.lower() or "interactive" in task_type.lower():
            return "realtime_chat"
        else:
            return "paper_summary"
