# 프론트엔드 실행 가이드

이 문서는 PaperPulse 프로젝트의 프론트엔드를 실행하는 단계별 가이드입니다.

## 1. `arxiv_paper_system/frontend` 디렉토리로 이동

```bash
cd D:\PaperPulse\arxiv_paper_system\frontend
```

## 2. Node.js 의존성 설치

프론트엔드 프로젝트에 필요한 Node.js 패키지를 설치합니다. 이 작업은 처음 한 번만 수행하면 되며, `package.json` 파일이 변경될 때 다시 실행할 수 있습니다.

```bash
npm install
```

## 3. 프론트엔드 개발 서버 실행

의존성 설치가 완료되면 다음 명령을 사용하여 프론트엔드 개발 서버를 시작합니다:

```bash
npm start
```

이 명령을 실행하면 일반적으로 브라우저에서 `http://localhost:3000` (또는 다른 포트)으로 프론트엔드 애플리케이션이 열립니다. 