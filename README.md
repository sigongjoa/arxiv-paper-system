# PaperShorts 인증 기반 댓글 시스템

학술 논문 토론을 위한 신뢰도 기반 인증 시스템입니다.

## 기능

### 인증 레벨
- **ORCID 인증**: 연구자 신원 확인 (최고 신뢰도)
- **DOI 인증**: 논문 저자 검증
- **학생 인증**: 대학 이메일 검증
- **게스트**: 일반 사용자 (승인 필요)

### 주요 기능
- 다단계 OAuth 인증 시스템
- 신뢰도 기반 댓글 필터링
- CrossRef API 연동 저자 검증
- 학생 이메일 인증 (.ac.kr, .edu 도메인)
- 관리자 승인 워크플로우
- JWT 기반 보안 토큰 관리

## 설치 및 실행

### 사전 요구사항
- Node.js 18+
- PostgreSQL 13+
- SMTP 서버 (이메일 발송용)

### 1. 데이터베이스 설정

PostgreSQL에서 데이터베이스를 생성합니다:

```sql
CREATE DATABASE paper_shorts_auth;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE paper_shorts_auth TO postgres;
```

### 2. 백엔드 설정

```bash
cd backend

# 의존성 설치
npm install

# 환경설정 파일 생성
cp .env.example .env

# .env 파일 편집 (필수)
# - 데이터베이스 설정
# - JWT 시크릿 키
# - ORCID 클라이언트 정보
# - SMTP 설정

# 데이터베이스 마이그레이션
npm run build
npm run migrate up

# 개발 서버 실행
npm run dev
```

### 3. 프론트엔드 실행

```bash
# 간단한 HTTP 서버로 실행 (Python 사용)
cd frontend
python -m http.server 3000

# 또는 Node.js http-server 사용
npx http-server -p 3000
```

### 4. 테스트

브라우저에서 `http://localhost:3000`에 접속하여 테스트합니다.

## ORCID 설정

1. [ORCID 개발자 도구](https://orcid.org/developer-tools)에서 애플리케이션 등록
2. Redirect URI: `http://localhost:3001/api/auth/orcid/callback`
3. `.env` 파일에 클라이언트 ID와 시크릿 추가

```env
ORCID_CLIENT_ID=your-client-id
ORCID_CLIENT_SECRET=your-client-secret
```

## API 엔드포인트

### 인증
- `POST /api/auth/login` - 일반 로그인
- `POST /api/auth/register` - 회원가입
- `GET /api/auth/orcid/login` - ORCID 인증 시작
- `GET /api/auth/orcid/callback` - ORCID 콜백
- `POST /api/auth/doi/verify` - DOI 저자 검증
- `POST /api/auth/student/email-request` - 학생 이메일 인증 요청
- `GET /api/auth/student/email-verify` - 이메일 인증 확인
- `GET /api/auth/profile` - 사용자 프로필

### 댓글
- `POST /api/comments` - 댓글 작성
- `GET /api/comments/paper/:paperId` - 논문별 댓글 조회
- `GET /api/comments/:commentId` - 특정 댓글 조회

### 관리자
- `GET /api/admin/comments/pending` - 승인 대기 댓글
- `PATCH /api/admin/comments/:id/approve` - 댓글 승인
- `GET /api/admin/users` - 사용자 목록
- `GET /api/admin/stats` - 시스템 통계

## 보안 설정

### 환경변수
```env
# 강력한 JWT 시크릿 키 사용
JWT_SECRET=your-super-secure-secret-key

# HTTPS 사용 (프로덕션)
NODE_ENV=production

# CORS 설정
FRONTEND_URL=https://your-domain.com
```

### Rate Limiting
- 일반 API: 100 요청/분
- 인증 API: 5 요청/분
- 댓글 작성: 10 요청/분
- 인증 시도: 3 요청/5분

## 데이터베이스 명령어

```bash
# 테이블 생성
npm run migrate up

# 테이블 삭제
npm run migrate down

# 데이터베이스 리셋
npm run migrate reset
```

## 디버깅

### 로그 확인
서버 콘솔에서 실시간 로그를 확인할 수 있습니다:
- 인증 요청
- 데이터베이스 쿼리 오류
- API 요청/응답

### 일반적인 문제
1. **ORCID 인증 실패**: 클라이언트 ID/시크릿 확인
2. **이메일 발송 실패**: SMTP 설정 확인
3. **DOI 검증 실패**: CrossRef User-Agent 설정 확인
4. **데이터베이스 연결 실패**: 연결 정보 및 권한 확인

## 라이센스

MIT License

## 기여

이슈 신고 및 풀 리퀘스트를 환영합니다.
