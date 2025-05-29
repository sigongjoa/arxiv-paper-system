import React from 'react';
import PaperList from './components/PaperList';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="AppHeader">
        <h1>arXiv Paper Management System</h1>
      </header>
      <main className="AppMain">
        <PaperList />
      </main>
    </div>
  );
}

export default App;
