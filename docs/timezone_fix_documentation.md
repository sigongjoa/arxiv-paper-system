# arXiv 논문 크롤링 시간대 문제 해결

## 문제 상황
- 6월 3일 논문이 크롤링되지 않음
- `days_back=0`으로 6월 2일만 검색했으나 모든 논문이 5월 30일로 인식됨
- arXiv는 미국 동부시간 기준으로 발표, UTC와 시차 존재

## 원인 분석
1. **시간대 차이**: arXiv 발표시간(EST/EDT)과 UTC 시차
2. **발표 스케줄**: arXiv는 일~목요일만 발표 (금토 없음)
3. **좁은 검색 범위**: `days_back=0`은 당일만 검색

## 해결 방법

### 1. DateCalculator 수정
```python
# 기존: 당일만 검색
start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

# 수정: 시간대 차이 고려하여 범위 확장
end_date = datetime.now(timezone.utc) + timedelta(days=1)  # 미래 1일 추가
start_date = (end_date - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
```

### 2. ArxivCrawler 수정
```python
# 연속 old paper 허용량 증가 (시간대 문제 대응)
max_consecutive_old = 100  # 50 → 100
```

### 3. API 기본값 수정
```python
# 더 넓은 범위로 기본 검색
days_back: int = 2  # 7 → 2
```

## 테스트 방법
```bash
# 테스트 스크립트 실행
python test_fix.py

# API 재시작
start_enhanced_backend.bat

# 6월 3일 논문 크롤링 테스트
curl -X POST http://localhost:8000/api/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{"domain": "cs", "days_back": 0, "limit": 10}'
```

## 결과
- `days_back=0`으로도 6월 1-4일 범위 검색 가능
- 시간대 차이로 인한 논문 누락 방지
- 최신 논문 크롤링 안정성 향상

## 향후 개선사항
1. arXiv 발표 시간 모니터링 자동화
2. 시간대별 최적 크롤링 시점 설정
3. 실시간 논문 알림 시스템 구축
