# arXiv Date Range Filtering Fix

## 문제
- 2025-05-30 논문들이 있는데 검색 범위가 2025-05-31부터 시작해서 모두 제외됨
- GUI에서 논문 수가 0개로 표시됨

## 해결방법
1. 날짜 범위를 2일 더 넓게 설정 (days_back + 2)
2. 최근 5일 이내 논문은 모두 포함
3. 10일 이상 오래된 논문만 제외
4. consecutive_old_papers 임계값 20으로 증가

## 수정 내용
### routes.py
```python
# Before
start_date = end_date - timedelta(days=days_back)

# After
start_date = end_date - timedelta(days=days_back + 2)  # 2일 더 넓게
```

### arxiv_crawler.py  
```python
# Before
if start_date <= paper.published_date <= end_date:

# After
days_diff = (end_date - paper.published_date).days
if days_diff <= 5:  # 5일 이내는 모두 포함
```

## 테스트
서버 재시작 후 크롤링하면 최신 논문들이 포함될 것
