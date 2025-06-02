const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3002;

// 정적 파일 서빙
app.use(express.static(__dirname));

// 메인 페이지 (게시판)
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// 로그인/회원가입 페이지 (기존 auth 페이지)
app.get('/auth', (req, res) => {
  res.sendFile(path.join(__dirname, 'auth.html'));
});

// SPA 라우팅을 위한 fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`
🚀 Frontend server is running on port ${PORT}
📱 Main App: http://localhost:${PORT}
🔐 Auth Page: http://localhost:${PORT}/auth
🔗 Backend API: http://localhost:3001/api
  `);
});
