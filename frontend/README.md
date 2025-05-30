# arXiv Paper Management System - Frontend

React 기반 프론트엔드 애플리케이션

## 구조

```
src/
├── components/          # 각 페이지 컴포넌트
│   ├── PaperList.js    # 논문 검색/관리
│   ├── Newsletter.js   # 뉴스레터 자동화
│   ├── MailingConfig.js # 메일링 설정
│   ├── PDFViewer.js    # PDF 뷰어
│   ├── MailingSend.js  # 메일 전송
│   └── WebPDFViewer.js # 웹 PDF 뷰어
├── styles/
│   └── common.css      # 공통 스타일
├── App.js              # 메인 앱 컴포넌트
├── App.css            # 앱 스타일
└── index.js           # 엔트리 포인트
```

## 실행

```bash
cd frontend
npm start
```

## 빌드

```bash
npm run build
```

## 주요 기능

- **논문 관리**: arXiv 논문 검색, 필터링, 저장
- **뉴스레터**: AI 요약과 함께 자동 뉴스레터 생성
- **메일링**: SMTP 설정 및 대량 메일 전송
- **PDF 뷰어**: 로컬/웹 PDF 파일 뷰어

## API 연동

백엔드 API 엔드포인트:
- `/api/papers/*` - 논문 관련
- `/api/newsletter/*` - 뉴스레터 관련  
- `/api/config/*` - 설정 관련
- `/api/pdfs/*` - PDF 관련

에러 로깅은 console.error로 처리, try-catch 필수 사용
