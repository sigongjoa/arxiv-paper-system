# arXiv to Shorts - 웹 로그 및 비디오 프리뷰 업데이트

## 새로운 기능

### 1. 실시간 로그 출력
- **Process 탭**에 실시간 로그 섹션 추가
- 터미널에서 보이는 모든 로그가 웹에서도 실시간으로 표시
- Clear Log 버튼으로 로그 화면 정리 가능

### 2. 비디오 프리뷰 개선
- **Preview 탭**에서 생성된 모든 비디오 목록 표시
- 드롭다운으로 비디오 선택 가능
- 비디오 정보 (파일명, 크기, 생성일) 표시
- 자동 새로고침 및 수동 새로고침 버튼

## 사용 방법

### 웹 서버 시작
```bash
cd D:\arxiv-to-shorts
python backend\app.py
```

### 웹 인터페이스 접속
- http://localhost:5000

### Process 탭에서 로그 확인
1. arXiv ID 입력 후 Process 실행
2. Process 탭에서 실시간 로그 확인
3. 각 단계별 진행 상황과 상세 로그 동시 모니터링

### Preview 탭에서 비디오 확인
1. Preview 탭으로 이동
2. 비디오 목록에서 원하는 비디오 선택
3. 자동으로 비디오 플레이어에 로드됨
4. 비디오 정보 확인 가능

## 기술적 변경사항

### 백엔드
- `backend/log_stream.py`: 로그 캡처 시스템
- `backend/app.py`: SSE 로그 스트리밍 API, 비디오 목록 API
- `backend/processor_impl.py`: 상세 로깅 추가
- `backend/core/pipeline.py`: 단계별 로깅 추가

### 프론트엔드
- `frontend/templates/index.html`: 로그 섹션, 비디오 선택기 추가
- `frontend/static/styles.css`: 로그 및 프리뷰 스타일링
- `frontend/static/app.js`: 실시간 로그, 비디오 로딩 기능

## API 엔드포인트

### 로그 관련
- `GET /api/logs`: 기존 로그 조회
- `GET /api/logs/stream`: 실시간 로그 스트림 (SSE)

### 비디오 관련
- `GET /api/videos`: 비디오 목록 조회
- `GET /output/videos/{filename}`: 비디오 파일 다운로드

## 로그 출력 예시
```
[14:30:15] Starting paper processing for arXiv ID: 2301.07041
[14:30:16] Fetching paper data from arXiv API...
[14:30:17] Successfully processed paper: Example Paper Title
[14:30:18] Starting video pipeline for paper: Example Paper Title
[14:30:19] Step 1/5: Generating script...
[14:30:25] Step 2/5: Creating visual materials...
[14:30:35] Step 3/5: Generating narration...
[14:30:45] Step 4/5: Composing video...
[14:31:10] Step 5/5: Publishing video...
[14:31:12] Pipeline completed successfully for 2301.07041
```
