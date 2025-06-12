# 백엔드 실행 가이드

이 문서는 PaperPulse 프로젝트의 백엔드를 실행하는 단계별 가이드입니다.

## 1. `arxiv_paper_system/backend` 디렉토리로 이동

```bash
cd D:\PaperPulse\arxiv_paper_system\backend
```

## 2. 가상 환경 생성 및 활성화

### 가상 환경 생성 (최초 1회만 실행)

```bash
python -m venv venv
```

### 가상 환경 활성화

Windows PowerShell을 사용하고 계시므로 다음 명령을 실행합니다:

```bash
.\venv\Scripts\Activate.ps1
```
가상 환경이 활성화되면 터미널 프롬프트 앞에 `(venv)`와 같은 표시가 나타납니다.

## 3. Python 패키지 설치

가상 환경이 활성화된 상태에서 필요한 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```

만약 `uvicorn`이 `requirements.txt`에 없거나 설치되지 않는다면, 다음을 추가로 실행합니다:

```bash
pip install uvicorn
```

## 4. 백엔드 애플리케이션 실행

`arxiv_paper_system` 디렉토리로 이동한 후 `PYTHONPATH`를 설정하고 `uvicorn`을 실행합니다.

먼저, `arxiv_paper_system` 디렉토리로 이동합니다:

```bash
cd D:\PaperPulse\arxiv_paper_system
```

다음 명령을 실행하여 백엔드를 시작합니다:

```bash
$env:PYTHONPATH = "D:\PaperPulse\arxiv_paper_system"; uvicorn backend.api.main:app --reload
```

이제 백엔드 애플리케이션이 `http://127.0.0.1:8000`에서 실행될 것입니다. 