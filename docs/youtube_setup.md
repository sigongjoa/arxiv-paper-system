# YouTube API 설정 가이드

이 문서는 YouTube API를 사용하여 비디오를 업로드하기 위한 설정 과정을 설명합니다.

## 1. Google Cloud Console 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트를 생성하거나 기존 프로젝트 선택
3. 프로젝트 이름 설정 (예: "arXiv to Shorts")

## 2. YouTube Data API v3 활성화

1. Google Cloud Console에서 "API 및 서비스" > "라이브러리"로 이동
2. "YouTube Data API v3" 검색
3. API 선택 후 "사용" 버튼 클릭

## 3. OAuth 2.0 클라이언트 ID 생성

1. "API 및 서비스" > "사용자 인증 정보"로 이동
2. "+ 사용자 인증 정보 만들기" > "OAuth 클라이언트 ID" 선택
3. 애플리케이션 유형: "웹 애플리케이션" 선택
4. 이름 설정 (예: "arXiv to Shorts Web Client")

### 승인된 JavaScript 원본
```
http://localhost:5000
```

### 승인된 리디렉션 URI
```
http://localhost:5000/api/youtube/callback
```

5. "만들기" 버튼 클릭

## 4. 클라이언트 시크릿 파일 다운로드

1. 생성된 OAuth 클라이언트 옆의 다운로드 아이콘 클릭
2. JSON 파일 다운로드
3. 파일 이름을 `youtube_credentials.json`으로 변경
4. `config/` 폴더에 저장

## 5. OAuth 동의 화면 설정

1. "OAuth 동의 화면" 메뉴로 이동
2. 사용자 유형: "외부" 선택 (개인 개발자의 경우)
3. 필수 정보 입력:
   - 앱 이름: "arXiv to Shorts"
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일

## 6. 스코프 추가

1. OAuth 동의 화면 설정에서 "범위" 섹션으로 이동
2. "범위 추가 또는 삭제" 클릭
3. 다음 스코프 추가:
   - `https://www.googleapis.com/auth/youtube.upload`

## 7. 테스트 사용자 추가 (개발 단계)

1. OAuth 동의 화면 설정에서 "테스트 사용자" 섹션으로 이동
2. "+ 사용자 추가" 클릭
3. YouTube 업로드에 사용할 Google 계정 이메일 추가

## 8. 파일 구조 확인

프로젝트 루트에서 다음 구조가 되어야 합니다:

```
arxiv-to-shorts/
├── config/
│   ├── youtube_credentials.json  # Google Cloud Console에서 다운로드한 파일
│   ├── youtube_token.json       # 최초 인증 후 자동 생성
│   └── oauth_state.json         # OAuth 상태 검증용 (자동 생성)
└── ...
```

## 9. 웹 기반 YouTube 인증 테스트

1. Flask 앱 실행: `python backend/app.py`
2. 브라우저에서 `http://localhost:5000` 접속
3. "Publish" 탭으로 이동
4. "🔗 Connect YouTube" 버튼 클릭
5. 팝업 창에서 Google 계정으로 로그인 및 권한 승인
6. 인증 성공 시 버튼이 "✓ YouTube Connected"로 변경
7. YouTube Shorts 체크박스 활성화 확인

## 주의사항

- YouTube API 할당량: 일일 10,000 유닛 (기본)
- 비디오 업로드: 1회당 약 1,600 유닛 소모
- 개발 단계에서는 테스트 사용자만 인증 가능
- 실제 배포 시에는 OAuth 동의 화면 검토 과정 필요
- 웹 기반 OAuth 플로우로 변경됨 (터미널 입력 불필요)

## 트러블슈팅

### 인증 오류가 발생하는 경우

1. `config/youtube_token.json` 및 `config/oauth_state.json` 파일 삭제 후 재인증
2. OAuth 클라이언트 ID의 리디렉션 URI 확인: `http://localhost:5000/api/youtube/callback`
3. 테스트 사용자 목록에 계정이 추가되었는지 확인
4. YouTube Data API v3가 활성화되었는지 확인
5. 스코프 `youtube.upload`가 추가되었는지 확인

### 팝업 차단 문제

1. 브라우저 팝업 차단 해제
2. 시크릿 모드에서 테스트

### 업로드 실패 시

1. YouTube API 할당량 확인
2. 동영상 파일 크기 및 형식 확인 (MP4 권장)
3. 네트워크 연결 상태 확인
4. 인증 상태 확인 ("✓ YouTube Connected" 표시되는지)

## API 엔드포인트

새로 추가된 YouTube 인증 관련 API:

- `GET /api/youtube/status` - 인증 상태 확인
- `GET /api/youtube/auth` - 인증 URL 생성
- `GET /api/youtube/callback` - OAuth 콜백 처리
