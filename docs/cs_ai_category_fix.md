# ArXiv 크롤링 오류 해결 - cs.AI 카테고리 확장

## 문제점
- 5월 30일 논문만 출력되고 6월 논문이 나오지 않음
- cs.AI 카테고리에만 검색하고 있었음
- 실제로 cs.AI 카테고리에는 6월 논문이 거의 없음 (arXiv 웹사이트 확인됨)

## 원인
1. `routes.py`에서 `category='cs.AI'`로 단일 카테고리만 검색
2. AI 논문들이 주로 cs.LG, cs.CL, cs.CV 등에 더 많이 올라감
3. cs.AI는 상대적으로 작은 카테고리

## 해결책
`crawl_papers_by_domain` 함수 수정:
```python
# AI 관련 카테고리는 확장해서 검색
if category == 'cs.AI':
    categories = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV']  # AI 관련 주요 카테고리
    print(f"DEBUG: Expanding cs.AI to include related categories: {categories}")
else:
    categories = [category]
```

## 수정된 카테고리
- cs.AI (Artificial Intelligence)
- cs.LG (Machine Learning) 
- cs.CL (Computation and Language)
- cs.CV (Computer Vision)

## 결과
이제 cs.AI 검색 시 AI 관련 4개 주요 카테고리에서 최신 논문을 수집

## 날짜
2025-06-03
