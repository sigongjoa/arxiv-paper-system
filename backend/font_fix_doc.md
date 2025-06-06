# 폰트 문제 해결 완료

## 문제
- 한글 폰트가 깨지는 문제
- backend/fonts 디렉토리에 폰트 파일 없음

## 해결
1. **research_template.py** 수정
   - Windows 기본 한글 폰트 경로 추가: `C:/Windows/Fonts/malgun.ttf`
   - NanumGothic.ttf 백업 경로 설정
   - 에러 로깅 추가

2. **title_card_generator.py** 수정  
   - 동일한 한글 폰트 경로 적용
   - 폰트 로딩 실패 시 로깅

## 적용된 폰트 우선순위
1. `backend/fonts/NanumGothic.ttf` (사용자 폰트)
2. `C:/Windows/Fonts/malgun.ttf` (시스템 기본)
3. `ImageFont.load_default()` (최종 백업)

## 테스트
`python test_font.py` 실행으로 폰트 로딩 검증

## 결과
한글 텍스트 렌더링 정상 동작
