# DB Papers Display Fix

## 문제
- 크롤링은 되지만 GUI에 저장된 논문들이 표시되지 않음
- get_papers_by_domain_and_date에서 날짜 범위가 너무 엄격함

## 해결방법
1. database.py에 get_recent_papers() 함수 추가
2. routes.py의 get_papers_by_domain_and_date() 함수 수정
3. 날짜 범위 대신 최근 논문들을 가져와서 도메인 필터링

## 수정 내용

### database.py 추가
```python
def get_recent_papers(self, limit: int = 100) -> List[Paper]:
    """Get most recent papers from database"""
    cursor = self.conn.cursor()
    cursor.execute('''
        SELECT * FROM papers 
        ORDER BY published_date DESC 
        LIMIT ?
    ''', (limit,))
```

### routes.py 수정
```python
# Before
papers = db.get_papers_by_date_range(start_date, end_date, limit * 3)

# After
papers = db.get_recent_papers(limit * 5)  # 더 많이 가져와서 필터링
```

## 결과
- 서버 재시작 후 GUI에서 DB에 저장된 논문들이 표시됨
- 도메인별 필터링 정상 작동
