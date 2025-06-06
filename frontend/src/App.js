import React, { useState, Suspense, lazy } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import './styles/common.css';
import './styles/recommendation.css';
import './App.css';

const PaperList = lazy(() => import('./components/PaperList'));
const Newsletter = lazy(() => import('./components/Newsletter'));
const MailingConfig = lazy(() => import('./components/MailingConfig'));
const PDFViewer = lazy(() => import('./components/PDFViewer'));
const MailingSend = lazy(() => import('./components/MailingSend'));
const WebPDFViewer = lazy(() => import('./components/WebPDFViewer'));
const RecommendationSystem = lazy(() => import('./components/RecommendationSystem'));
const CitationGraph = lazy(() => import('./components/CitationGraph'));
const CrawlingSystem = lazy(() => import('./components/CrawlingSystem'));
const AIAssistant = lazy(() => import('./components/ai/AIAssistant'));
const ResearchAgents = lazy(() => import('./components/ai/ResearchAgents'));
const SystemDashboard = lazy(() => import('./components/SystemDashboard'));

function App() {
  const [activeTab, setActiveTab] = useState('crawling');
  const [crawlingSubTab, setCrawlingSubTab] = useState('setup');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 크롤링 결과 탭으로 전환하는 함수
  const switchToCrawlingResults = () => {
    setCrawlingSubTab('results');
  };

  // 전역 함수로 등록
  React.useEffect(() => {
    window.switchToCrawlingResults = switchToCrawlingResults;
    return () => {
      delete window.switchToCrawlingResults;
    };
  }, []);

  const tabs = [
    { id: 'crawling', label: 'Multi-Platform Crawling', icon: 'fas fa-rocket', component: CrawlingSystem },
    { id: 'papers', label: 'Paper Analysis', icon: 'fas fa-microscope', component: PaperList },
    { id: 'ai-assistant', label: 'AI Assistant', icon: 'fas fa-robot', component: AIAssistant },
    { id: 'research-agents', label: 'Research Agents', icon: 'fas fa-brain', component: ResearchAgents },
    { id: 'recommendations', label: 'Smart Recommendations', icon: 'fas fa-lightbulb', component: RecommendationSystem },
    { id: 'citation', label: 'Citation Intelligence', icon: 'fas fa-project-diagram', component: CitationGraph },
    { id: 'newsletter', label: 'Auto Newsletter', icon: 'fas fa-newspaper', component: Newsletter },
    { id: 'system', label: 'System Status', icon: 'fas fa-tachometer-alt', component: SystemDashboard },
    { id: 'config', label: 'Configuration', icon: 'fas fa-cog', component: MailingConfig },
    { id: 'pdf', label: 'PDF Manager', icon: 'fas fa-file-pdf', component: PDFViewer },
    { id: 'send', label: 'Mail Sender', icon: 'fas fa-paper-plane', component: MailingSend },
    { id: 'webpdf', label: 'Web PDF', icon: 'fas fa-globe', component: WebPDFViewer }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="AppLayout enhanced">
      <header className="AppHeader enhanced">
        <div className="HeaderContainer">
          <h1 className="AppTitle enhanced">
            <span className="TitleIcon">🤖</span>
            Enhanced arXiv Analysis System
            <span className="VersionBadge">v2.0</span>
          </h1>
          <p className="AppSubtitle">AI-Powered Research Assistant</p>
        </div>
      </header>
      
      <div className="AppBody enhanced">
        <nav className={`SidebarNav enhanced ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <button 
            className="SidebarToggle" 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? 'Expand' : 'Collapse'}
          >
            <i className={`fas ${sidebarCollapsed ? 'fa-chevron-right' : 'fa-chevron-left'}`}></i>
          </button>
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`SidebarButton enhanced ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              title={tab.label}
            >
              <i className={tab.icon}></i>
              <span className="SidebarLabel">{tab.label}</span>
            </button>
          ))}
          
          {activeTab === 'crawling' && (
            <div className="SidebarSubNavigation">
              <button 
                className={`SidebarSubButton ${crawlingSubTab === 'setup' ? 'active' : ''}`}
                onClick={() => setCrawlingSubTab('setup')}
              >
                <i className="fas fa-cog"></i>
                <span className="SidebarLabel">Crawling Setup</span>
              </button>
              <button 
                className={`SidebarSubButton ${crawlingSubTab === 'results' ? 'active' : ''}`}
                onClick={() => setCrawlingSubTab('results')}
              >
                <i className="fas fa-chart-bar"></i>
                <span className="SidebarLabel">Crawling Results</span>
              </button>
            </div>
          )}
        </nav>
        
        <main className="MainContent enhanced">
          <div className="ContentWrapper">
            <ErrorBoundary>
              <Suspense fallback={<LoadingFallback />}>
                {activeTab === 'crawling' ? (
                  <CrawlingSystem activeSubTab={crawlingSubTab} />
                ) : (
                  ActiveComponent && <ActiveComponent />
                )}
              </Suspense>
            </ErrorBoundary>
          </div>
        </main>
      </div>
      
      <footer className="AppFooter">
        <div className="FooterContent">
          <span>© 2024 Enhanced arXiv Analysis System</span>
          <span>Powered by LM Studio & AI Agents</span>
        </div>
      </footer>
    </div>
  );
}

const LoadingFallback = () => (
  <div className="LoadingFallback">
    <div className="LoadingSpinner"></div>
    <p>Loading component...</p>
  </div>
);

export default App;
