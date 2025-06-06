# arXiv Date Filter Fix

## 문제
- arXiv API에서 2025-06-01 논문이 하나도 검색되지 않음
- 모든 논문의 updated_date가 2025-05-30으로 표시됨

## 해결방법
1. submittedDate 필터 사용
2. published_date 기준으로 필터링 변경
3. consecutive_old_papers 임계값 50으로 증가

## 수정 내용
```python
# Before
full_query = f'({category_query})'
if start_date <= paper.updated_date <= end_date:

# After  
date_filter = f'submittedDate:[{start_date.strftime("%Y%m%d")}0000 TO {end_date.strftime("%Y%m%d")}2359]'
full_query = f'({category_query}) AND {date_filter}'
if start_date <= paper.published_date <= end_date:
```

## 테스트 필요
크롤링으로 2025-06-01 데이터 확인
