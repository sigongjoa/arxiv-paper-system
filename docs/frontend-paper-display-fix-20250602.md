# Frontend Paper Display Fix

## 문제
- GUI에서 크롤링된 논문들이 표시되지 않음
- 초기 로드시 논문 목록이 비어있음
- 사용자가 수동으로 검색해야 함

## 해결방법
PaperList.js 컴포넌트 개선:
1. 컴포넌트 마운트시 자동으로 논문 로드
2. 더 나은 에러 처리와 디버깅
3. 논문이 없을 때 안내 메시지
4. 논문 개수 표시

## 수정 내용

### 자동 초기 로드
```javascript
useEffect(() => {
  const loadInitialPapers = async () => {
    setLoading(true);
    try {
      const response = await paperAPI.getPapers('cs', 7, 50, null);
      const papersData = response.data || [];
      setPapers(papersData);
    } catch (err) {
      console.error('ERROR: Failed to load initial papers:', err);
      setPapers([]);
    } finally {
      setLoading(false);
    }
  };
  
  loadInitialPapers();
}, []);
```

### 개선된 에러 처리
```javascript
console.log('DEBUG: API response:', response.data);
console.error('ERROR: handleDomainSearch failed:', {
  message: err.message,
  response: err.response?.data,
  status: err.response?.status
});
```

### 빈 상태 메시지
```javascript
{!loading && papers.length === 0 && !error && (
  <div className="Card">
    <div className="CardBody" style={{textAlign: 'center'}}>
      <p>논문을 찾을 수 없습니다. 크롤링을 먼저 실행해주세요.</p>
      <button onClick={handleCrawl}>크롤링 시작</button>
    </div>
  </div>
)}
```

### 논문 개수 표시
```javascript
<h3>총 {papers.length}개의 논문을 찾았습니다</h3>
```

## 결과
- 페이지 로드시 자동으로 DB의 논문들이 표시됨
- 논문이 없으면 크롤링 권유 메시지 표시
- 더 나은 사용자 경험과 디버깅

## 테스트
1. 프론트엔드 재시작: `npm start`
2. 브라우저에서 localhost:3000 접속
3. Paper Management 탭에서 논문 목록 확인
