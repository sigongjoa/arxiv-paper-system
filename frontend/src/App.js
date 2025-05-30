import React, { useState } from 'react';
import PaperList from './components/PaperList';
import Newsletter from './components/Newsletter';
import MailingConfig from './components/MailingConfig';
import PDFViewer from './components/PDFViewer';
import MailingSend from './components/MailingSend';
import WebPDFViewer from './components/WebPDFViewer';
import './styles/common.css';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('papers');

  const tabs = [
    { id: 'papers', label: 'Paper Management', icon: 'fas fa-file-alt', component: PaperList },
    { id: 'newsletter', label: 'Newsletter', icon: 'fas fa-newspaper', component: Newsletter },
    { id: 'config', label: 'Mailing Config', icon: 'fas fa-cog', component: MailingConfig },
    { id: 'pdf', label: 'PDF Viewer', icon: 'fas fa-file-pdf', component: PDFViewer },
    { id: 'send', label: 'Send Mail', icon: 'fas fa-paper-plane', component: MailingSend },
    { id: 'webpdf', label: 'Web PDF', icon: 'fas fa-globe', component: WebPDFViewer }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="App">
      <header className="AppHeader">
        <div className="AppContainer">
          <h1 className="AppTitle">arXiv Paper Management System</h1>
          <nav className="TabNav">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`TabButton ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <i className={tab.icon}></i> {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>
      <main className="AppMain">
        <div className="AppContainer">
          {ActiveComponent && <ActiveComponent />}
        </div>
      </main>
    </div>
  );
}

export default App;
