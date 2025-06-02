## tqdm 진행률 웹 표시 수정 완료

### 문제
- MoviePy의 tqdm 진행률이 터미널에서만 보이고 웹에서 안 보임
- 기존 로그 캡처가 logging 모듈만 캡처해서 stdout 출력 누락

### 해결책
1. **stdout 캡처 추가**: `StdoutCapture` 클래스로 모든 stdout 출력 캡처
2. **PROGRESS 로그 레벨**: tqdm 출력을 별도 레벨로 분류
3. **스타일링**: 파란색으로 진행률 표시

### 변경사항
- `backend/log_stream.py`: stdout 캡처 시스템 추가
- `frontend/static/styles.css`: PROGRESS 로그 스타일 추가

### 서버 재시작 필요
```bash
# 현재 서버 중지 (Ctrl+C)
# 다시 시작
python backend\app.py
```

이제 웹에서 MoviePy 진행률이 실시간으로 표시됩니다.
