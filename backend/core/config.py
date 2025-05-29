import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arxiv_papers.db")
LLM_API_URL = os.getenv("LLM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RATE_LIMIT_DELAY = 3.0
MAX_RESULTS_PER_REQUEST = 100
