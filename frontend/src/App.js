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
const SystemDashboard = lazy(() => import('./components/SystemDashboard'));

function App() {
  const [activeTab, setActiveTab] = useState('systemManagement'); // Initial active main tab
  const [activeSubTabMap, setActiveSubTabMap] = useState({
    'crawling': 'setup', // Default sub-tab for crawling
    'systemManagement': 'dashboard', // Default sub-tab for System Management
    'documentMailTools': 'pdfManager', // Default sub-tab for Document & Mail Tools
    'researchAnalysis': 'paperAnalysis', // Default sub-tab for Research & Analysis
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Helper function to update active sub-tab
  const handleSubTabClick = (parentTabId, subTabId) => {
    setActiveSubTabMap(prev => ({
      ...prev,
      [parentTabId]: subTabId,
    }));
    setActiveTab(parentTabId); // Ensure parent tab is active when a sub-tab is clicked
  };

  // 크롤링 결과 탭으로 전환하는 함수
  const switchToCrawlingResults = () => {
    handleSubTabClick('crawling', 'results');
  };

  // 전역 함수로 등록
  React.useEffect(() => {
    window.switchToCrawlingResults = switchToCrawlingResults;
    return () => {
      delete window.switchToCrawlingResults;
    };
  }, []);

  const tabs = [
    {
      id: 'crawling',
      label: 'Multi-Platform Crawling',
      icon: 'fas fa-rocket',
      subTabs: [
        { id: 'setup', label: 'Crawling Setup', icon: 'fas fa-cog', component: CrawlingSystem },
        { id: 'results', label: 'Crawling Results', icon: 'fas fa-chart-bar', component: CrawlingSystem }
      ]
    },
    {
      id: 'researchAnalysis',
      label: 'Research & Analysis',
      icon: 'fas fa-flask', // New icon for Research & Analysis
      subTabs: [
        { id: 'paperAnalysis', label: 'Paper Analysis', icon: 'fas fa-microscope', component: PaperList },
        { id: 'citationIntelligence', label: 'Citation Intelligence', icon: 'fas fa-project-diagram', component: CitationGraph }
      ]
    },
    {
      id: 'systemManagement',
      label: 'System Management',
      icon: 'fas fa-cogs', // New icon for System Management
      subTabs: [
        { id: 'dashboard', label: 'System Status', icon: 'fas fa-tachometer-alt', component: SystemDashboard },
        { id: 'config', label: 'Configuration', icon: 'fas fa-cog', component: MailingConfig },
        { id: 'newsletterConfig', label: 'Auto Newsletter', icon: 'fas fa-newspaper', component: Newsletter } 
      ]
    },
    {
      id: 'documentMailTools',
      label: 'Document & Mail Tools',
      icon: 'fas fa-tools', // New icon for Document & Mail Tools
      subTabs: [
        { id: 'pdfManager', label: 'PDF Manager', icon: 'fas fa-file-pdf', component: PDFViewer },
        { id: 'mailSender', label: 'Mail Sender', icon: 'fas fa-paper-plane', component: MailingSend },
        { id: 'webpdfViewer', label: 'Web PDF', icon: 'fas fa-globe', component: WebPDFViewer }
      ]
    }
  ];

  let ActiveComponent = null;
  let currentSubTabComponent = null;

  const currentActiveMainTab = tabs.find(tab => tab.id === activeTab);

  if (currentActiveMainTab) {
    if (currentActiveMainTab.subTabs) {
      const activeSubTabIdForParent = activeSubTabMap[activeTab];
      currentSubTabComponent = currentActiveMainTab.subTabs.find(
        subTab => subTab.id === activeSubTabIdForParent
      )?.component;
      ActiveComponent = currentSubTabComponent;
    } else {
      ActiveComponent = currentActiveMainTab.component;
    }
  }

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
            <React.Fragment key={tab.id}>
              <button
                className={`SidebarButton enhanced ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(tab.id);
                  if (tab.subTabs && !activeSubTabMap[tab.id]) {
                    handleSubTabClick(tab.id, tab.subTabs[0].id);
                  }
                }}
                title={tab.label}
              >
                <i className={tab.icon}></i>
                <span className="SidebarLabel">{tab.label}</span>
              </button>
              {activeTab === tab.id && tab.subTabs && (
                <div className="SidebarSubNavigation">
                  {tab.subTabs.map(subTab => (
                    <button
                      key={subTab.id}
                      className={`SidebarSubButton ${activeSubTabMap[tab.id] === subTab.id ? 'active' : ''}`}
                      onClick={() => handleSubTabClick(tab.id, subTab.id)}
                    >
                      <i className={subTab.icon}></i>
                      <span className="SidebarLabel">{subTab.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </React.Fragment>
          ))}
        </nav>
        
        <main className="MainContent enhanced">
          <div className="ContentWrapper">
            <ErrorBoundary>
              <Suspense fallback={<LoadingFallback />}>
                {ActiveComponent && <ActiveComponent activeSubTab={activeSubTabMap[activeTab]} />}
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
