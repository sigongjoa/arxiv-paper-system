# arXiv API Date Filter Issue Fix

## 문제
- arXiv API submittedDate 필터가 정상 작동하지 않음
- 6월 1-2일 논문 검색시 0개 결과 반환

## 해결방법
날짜 필터 제거하고 최신순 정렬만 사용, 클라이언트 측에서 날짜 필터링

## 수정 내용
```python
# Before
date_filter = f'submittedDate:[{start_date.strftime("%Y%m%d")}0000 TO {end_date.strftime("%Y%m%d")}2359]'
full_query = f'({category_query}) AND {date_filter}'

# After
full_query = f'({category_query})'
```

## 실제 날짜 확인
- 오늘: 2025-06-02 (월요일)
- arXiv에 최신 논문들 계속 업로드 중

## 테스트
서버 재시작 후 크롤링 테스트 필요
