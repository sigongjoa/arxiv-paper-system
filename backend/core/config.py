import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arxiv_papers.db")
LLM_API_URL = os.getenv("LLM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RATE_LIMIT_DELAY = 3.0
MAX_RESULTS_PER_REQUEST = 100

# Automation system config
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_SES_SENDER_EMAIL = os.getenv("AWS_SES_SENDER_EMAIL", "newsletter@example.com")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
NEWSLETTER_SCHEDULE_HOUR = int(os.getenv("NEWSLETTER_SCHEDULE_HOUR", "9"))
NEWSLETTER_SCHEDULE_MINUTE = int(os.getenv("NEWSLETTER_SCHEDULE_MINUTE", "0"))
AUTOMATION_WORKERS = int(os.getenv("AUTOMATION_WORKERS", "2"))
