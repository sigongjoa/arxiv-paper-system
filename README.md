# arXiv Paper Crawler with GUI

특정 카테고리와 기간의 arXiv 논문을 크롤링하고 관리하는 웹 GUI 시스템

## 설치
```cmd
cd D:\arxiv-paper-system
pip install -r requirements.txt
pip install fastapi uvicorn
```

## GUI 실행 (권장)
1. **서버 시작**: `start_server.bat` 실행
2. **GUI 열기**: `start_gui.bat` 실행

## CLI 실행
```cmd
python main.py
```

## 카테고리
- Computer Science: 29개 세부 카테고리
- Mathematics: 32개 세부 카테고리  
- Physics: 20개 세부 카테고리

## 기능
- 웹 GUI를 통한 직관적 조작
- 특정 도메인별 논문 크롤링
- 기간별 논문 검색 및 표시
- SQLite 데이터베이스 저장
- 논문 메타데이터 관리
- FastAPI 백엔드 서버

## 서버 API 엔드포인트
- `GET /api/v1/papers` - 논문 목록 조회
- `POST /api/v1/crawl` - 논문 크롤링 실행
- `GET /api/v1/stats` - 데이터베이스 통계
- `GET /api/v1/categories` - 카테고리 목록
- `GET /api/v1/health` - 서버 상태 확인
