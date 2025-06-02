# PaperShorts 시스템 성능 및 확장성 분석

## 현재 시스템 구조

### 백엔드 (Node.js + TypeScript)
- **데이터베이스**: SQLite (개발용)
- **웹 프레임워크**: Express.js
- **인증**: JWT 토큰
- **Rate Limiting**: 
  - 일반 요청: 100req/15min
  - 댓글 작성: 10req/5min
- **보안**: Helmet, CORS, bcrypt

### 프론트엔드 (Vanilla JS)
- **서버**: Express 정적 파일 서빙
- **SPA**: 클라이언트 사이드 라우팅
- **API 통신**: Fetch API

## 현재 처리 가능 인원

### 동시 접속자 기준
- **SQLite 한계**: ~1,000 동시 읽기, ~100 동시 쓰기
- **Rate Limiting**: 100req/15min = 6.67req/min/user
- **메모리 사용량**: ~50MB (기본) + ~10MB/1000 활성 세션

### 예상 처리 용량
```
낮은 활동 (읽기 위주): 5,000-10,000 동시 접속자
중간 활동 (댓글/투표): 1,000-3,000 동시 접속자  
높은 활동 (글 작성): 500-1,000 동시 접속자
```

## 병목 지점 및 개선방안

### 1. 데이터베이스 (가장 큰 병목)
**현재**: SQLite (단일 파일, 제한적 동시성)
**개선방안**:
- **PostgreSQL**: 10,000+ 동시 접속 지원
- **Redis**: 세션/캐시 저장소
- **Read Replica**: 읽기 성능 향상

### 2. 파일 업로드 (미구현)
**향후 필요시**:
- **AWS S3**: 파일 저장소
- **CloudFront**: CDN
- **이미지 처리**: Sharp 라이브러리

### 3. 인메모리 캐싱
**현재**: 없음
**개선방안**:
- **Node-cache**: 간단한 인메모리 캐시
- **Redis**: 분산 캐시

## 확장성 로드맵

### Phase 1: 소규모 (100-1,000 사용자)
- 현재 구조 유지
- PostgreSQL 마이그레이션
- 기본 모니터링 추가

### Phase 2: 중규모 (1,000-10,000 사용자)
- Redis 캐시 레이어
- Load Balancer
- CDN 도입
- Database connection pooling

### Phase 3: 대규모 (10,000+ 사용자)
- 마이크로서비스 분리
- Database sharding
- Message Queue (Redis Pub/Sub)
- Auto-scaling

## 모니터링 지표

### 핵심 메트릭
- **응답 시간**: <200ms (목표)
- **처리량**: req/sec
- **에러율**: <1%
- **CPU 사용률**: <70%
- **메모리 사용률**: <80%
- **DB 연결 수**: 모니터링 필요

## 비용 추정 (월간)

### 소규모 (1,000 사용자)
- **서버**: AWS t3.small ($20)
- **데이터베이스**: PostgreSQL ($20)
- **총 비용**: ~$50/월

### 중규모 (10,000 사용자)  
- **서버**: AWS t3.medium x2 ($70)
- **데이터베이스**: PostgreSQL ($100)
- **Redis**: ElastiCache ($50)
- **CDN**: CloudFront ($20)
- **총 비용**: ~$250/월

### 대규모 (100,000 사용자)
- **서버**: Auto-scaling group ($500)
- **데이터베이스**: RDS cluster ($800)
- **Redis**: ElastiCache cluster ($200)
- **CDN + Storage**: ($100)
- **총 비용**: ~$1,600/월

## 결론

현재 시스템은 **1,000-3,000명 동시 사용자**까지 안정적으로 처리 가능합니다.

주요 개선사항:
1. SQLite → PostgreSQL 마이그레이션 (우선순위 1)
2. Redis 캐시 레이어 추가
3. 모니터링 시스템 구축
4. Rate limiting 세분화

급격한 사용자 증가 시 단계적 확장 계획을 따라 진행하면 됩니다.
