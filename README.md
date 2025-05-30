# arXiv Paper Management System with Newsletter Automation

자동화 뉴스레터 GUI 통합 완료

## 새로운 기능

### Newsletter Automation Tab
- **논문 수집 및 요약**: 도메인별 최신 논문 자동 수집
- **LM Studio 연동**: Mistral 7B 모델로 AI 요약 생성
- **PDF 생성**: wkhtmltopdf로 뉴스레터 PDF 생성
- **이메일 전송**: AWS SES 통한 자동 이메일 발송
- **테스트 모드**: 실제 전송 없이 콘텐츠 생성 테스트
- **스케줄링**: 일일 뉴스레터 자동 스케줄링 (Placeholder)
- **시스템 모니터링**: LLM, 이메일, PDF 서비스 상태 확인

## 프론트엔드 실행

```bash
cd frontend
npm start
```

## 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

## LM Studio 설정

1. LM Studio 실행
2. Mistral 7B Q4_K_M 모델 로드
3. Server 탭에서 포트 1234로 실행
4. 백엔드가 자동으로 http://127.0.0.1:1234 연결

## AWS SES 설정 (선택사항)

환경변수 설정:
```
AWS_REGION=us-east-1
AWS_SES_SENDER_EMAIL=newsletter@yourdomain.com
```

## 사용방법

1. **Paper Management 탭**: 기존 논문 관리 기능
2. **Newsletter Automation 탭**: 
   - Create Newsletter: 즉시 뉴스레터 생성/전송
   - Schedule Daily: 일일 자동 뉴스레터 설정
   - System Status: 시스템 상태 모니터링

## 기술 스택

- **Frontend**: React, CSS (HTML 템플릿 스타일 적용)
- **Backend**: FastAPI, SQLite
- **AI**: LM Studio (Mistral 7B Q4_K_M)
- **PDF**: wkhtmltopdf
- **Email**: AWS SES
- **UI**: 기존 GUI와 일관된 디자인

기존 시스템과 완전 통합된 Newsletter Automation GUI 완료.