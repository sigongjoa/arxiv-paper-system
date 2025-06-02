from vllm import LLM, SamplingParams
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import asyncio
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="Local LLM API Server")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 1000

class LocalLLMServer:
    def __init__(self, model_name: str = "meta-llama/Llama-3.1-8B-Instruct"):
        self.model_name = model_name
        self.llm = None
        self.load_model()
        
    def load_model(self):
        try:
            print(f"Loading model: {self.model_name}")
            self.llm = LLM(
                model=self.model_name,
                tensor_parallel_size=1,
                gpu_memory_utilization=0.9,
                max_model_len=4096,
                trust_remote_code=True
            )
            print("Model loaded successfully")
        except Exception as e:
            logging.error(f"Model loading failed: {e}")
            # 백업 모델로 Phi-3 시도
            try:
                print("Trying backup model: microsoft/Phi-3-mini-4k-instruct")
                self.llm = LLM(
                    model="microsoft/Phi-3-mini-4k-instruct",
                    tensor_parallel_size=1,
                    gpu_memory_utilization=0.9,
                    max_model_len=4096
                )
                print("Backup model loaded successfully")
            except Exception as e2:
                logging.error(f"Backup model loading failed: {e2}")
                raise
    
    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 1000) -> str:
        try:
            # 메시지를 프롬프트로 변환
            prompt = self.format_messages(messages)
            
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=0.95,
                max_tokens=max_tokens,
                stop=["<|eot_id|>", "</s>"]
            )
            
            outputs = self.llm.generate([prompt], sampling_params)
            return outputs[0].outputs[0].text.strip()
            
        except Exception as e:
            logging.error(f"Generation error: {e}")
            raise
    
    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        formatted = "<|begin_of_text|>"
        for msg in messages:
            if msg["role"] == "system":
                formatted += f"<|start_header_id|>system<|end_header_id|>\n{msg['content']}<|eot_id|>"
            elif msg["role"] == "user":
                formatted += f"<|start_header_id|>user<|end_header_id|>\n{msg['content']}<|eot_id|>"
            elif msg["role"] == "assistant":
                formatted += f"<|start_header_id|>assistant<|end_header_id|>\n{msg['content']}<|eot_id|>"
        
        formatted += "<|start_header_id|>assistant<|end_header_id|>\n"
        return formatted

# 글로벌 LLM 서버 인스턴스
llm_server = None

@app.on_event("startup")
async def startup_event():
    global llm_server
    try:
        llm_server = LocalLLMServer()
    except Exception as e:
        logging.error(f"Failed to initialize LLM server: {e}")
        raise

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        response_text = llm_server.generate_response(
            messages, 
            request.temperature, 
            request.max_tokens
        )
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(response_text.split())
            }
        }
    except Exception as e:
        logging.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": llm_server.model_name if llm_server else "not loaded"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
