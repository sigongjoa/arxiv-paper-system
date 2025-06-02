# YouTube 업로드 설정 가이드

## 1. Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. API 및 서비스 > 라이브러리 > YouTube Data API v3 활성화
4. API 및 서비스 > 사용자 인증 정보 > OAuth 2.0 클라이언트 ID 생성
5. 애플리케이션 유형: 데스크톱 애플리케이션
6. 클라이언트 ID JSON 파일 다운로드

## 2. 인증 파일 설정

1. 다운로드한 JSON 파일을 `config/youtube_credentials.json`으로 저장
2. `.env` 파일에 YouTube API 정보 추가:
   ```
   YOUTUBE_CLIENT_ID=your_client_id_here
   YOUTUBE_CLIENT_SECRET=your_client_secret_here
   ```

## 3. 첫 업로드 시 인증

- 첫 업로드 시 브라우저에서 인증 필요
- 인증 후 토큰이 `config/youtube_token.json`에 자동 저장
- 이후 업로드는 자동으로 인증됨

## 4. 업로드 사용법

1. 비디오 생성 완료 후 Publish 탭으로 이동
2. 업로드할 비디오 선택
3. 제목, 설명, 해시태그 입력
4. YouTube 체크박스 선택
5. "🚀 Publish Now" 버튼 클릭

## 주의사항

- YouTube API 할당량 제한 있음 (일일 10,000 units)
- 업로드된 비디오는 기본적으로 공개 상태
- 채널 소유자만 업로드 가능
