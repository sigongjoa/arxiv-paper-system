# arXiv Newsletter Automation System

자동화 서비스 구현 완료

## 설치

```bash
cd backend
pip install -r requirements.txt
```

## 환경 설정

.env 파일에 다음 추가:
```
AWS_REGION=us-east-1
AWS_SES_SENDER_EMAIL=newsletter@yourdomain.com
REDIS_HOST=localhost
REDIS_PORT=6379
NEWSLETTER_SCHEDULE_HOUR=9
NEWSLETTER_SCHEDULE_MINUTE=0
AUTOMATION_WORKERS=2
```

## 실행

```bash
python automation_main.py
```

## 구성 요소

- **EmailService**: AWS SES 이메일 전송
- **PdfGenerator**: Puppeteer PDF 생성
- **QueueManager**: Redis 큐 시스템
- **NewsletterService**: 뉴스레터 생성/전송
- **TaskScheduler**: 작업 스케줄링
- **AutomationManager**: 전체 시스템 관리

## 주요 기능

1. 자동화 시스템 시작/중지
2. 수동 뉴스레터 생성
3. 일일 뉴스레터 스케줄링
4. 시스템 상태 모니터링

문서 기반으로 Mistral 7B Q4_K_M 모델, AWS SES, Redis+Celery 큐 시스템 구현 완료.
