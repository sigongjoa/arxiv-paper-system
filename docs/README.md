# arXiv Paper Management System

## 🚀 시스템 실행

### 메인 시스템 시작
```bat
D:\arxiv-paper-system\start_system.bat
```

## 📋 주요 기능

### 1. 📊 Collection (논문 수집)
- **위치**: `frontend/public/data-collection.html`
- **기능**: 
  - 도메인별 논문 크롤링 (Computer Science, Math, Physics)
  - 카테고리별 세부 검색
  - 데이터베이스 통계 확인

### 2. 🔍 Search (논문 검색)
- **위치**: `frontend/public/arxiv-search.html`
- **기능**:
  - 키워드 기반 검색
  - 카테고리별 빠른 검색
  - 실시간 검색 결과

### 3. 📋 Results (검색 결과)
- **위치**: `frontend/public/arxiv-results.html`
- **기능**:
  - 검색 결과 표시
  - 논문 분석 기능
  - PDF 링크 제공

### 4. 📋 Summaries (논문 요약)
- **위치**: `frontend/public/paper-summary.html`
- **기능**:
  - AI 기반 논문 분석
  - 구조화된 요약 제공
  - 섹션별 내용 정리

## 🌐 네비게이션

모든 페이지 상단에 통합 네비게이션 바 제공:
- **arXiv Manager** (브랜드 로고)
- **📊 Collection** - 논문 수집 메인
- **🔍 Search** - 검색 기능
- **📋 Summaries** - 논문 요약

## 📱 반응형 디자인

- 데스크톱/모바일 완전 지원
- 모바일에서 햄버거 메뉴 제공
- 터치 친화적 인터페이스

## 🔧 API 엔드포인트

백엔드 서버: `http://localhost:8000`

- `GET /api/v1/papers` - 논문 목록 조회
- `POST /api/v1/search` - 논문 검색
- `POST /api/v1/crawl` - 논문 크롤링
- `POST /api/v1/papers/analyze` - 논문 분석
- `GET /api/v1/stats` - 데이터베이스 통계

## 📁 파일 구조

```
D:\arxiv-paper-system\
├── frontend\
│   └── public\
│       ├── index.html          # 메인 인덱스
│       ├── data-collection.html # 논문 수집
│       ├── arxiv-search.html    # 검색 메인
│       ├── arxiv-results.html   # 검색 결과
│       └── paper-summary.html   # 논문 요약
├── backend\
│   └── api\
├── start_system.bat            # 시스템 시작
└── docs\
    └── README.md              # 이 파일
```

## 🎯 사용 순서

1. `start_system.bat` 실행
2. 브라우저에서 자동으로 메인 페이지 열림
3. 네비게이션을 통해 원하는 기능 접근:
   - 새 논문 수집 → Collection
   - 논문 검색 → Search  
   - 분석된 논문 보기 → Summaries

## ⚡ 빠른 시작

1. 시스템 시작: `start_system.bat`
2. Collection에서 논문 크롤링 실행
3. Search에서 키워드 검색
4. Summaries에서 AI 분석 결과 확인

## 🔍 검색 팁

- 키워드 검색: `machine learning`
- 카테고리 검색: `cat:cs.AI`
- 저자 검색: `au:Smith`
- 조합 검색: `machine learning AND computer vision`
