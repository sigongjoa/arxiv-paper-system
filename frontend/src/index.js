import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

window.addEventListener('error', (e) => {
  console.error('ERROR:', JSON.stringify({
    timestamp: new Date().toISOString(),
    level: 'ERROR', 
    message: e.message,
    trace: e.error?.stack || e.filename + ':' + e.lineno
  }));
});

window.addEventListener('unhandledrejection', (e) => {
  console.error('ERROR:', JSON.stringify({
    timestamp: new Date().toISOString(),
    level: 'ERROR',
    message: e.reason?.message || e.reason,
    trace: e.reason?.stack || 'Promise rejection'
  }));
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
