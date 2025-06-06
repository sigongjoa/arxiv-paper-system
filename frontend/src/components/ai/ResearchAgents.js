import React, { useState, useEffect } from 'react';
import './ResearchAgents.css';
import PaperAnalysisPanel from './PaperAnalysisPanel';
import ResearchDiscoveryPanel from './ResearchDiscoveryPanel';
import CitationNetworkPanel from './CitationNetworkPanel';
import SystemStatusPanel from './SystemStatusPanel';

const ResearchAgents = () => {
  const [activeTab, setActiveTab] = useState('status');
  const [systemStatus, setSystemStatus] = useState({
    orchestrator_status: 'unknown',
    llm_connection: false,
    agents: {},
    active_workflows: 0
  });
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('/api/agents/status');
      const data = await response.json();
      
      if (data.success) {
        setSystemStatus(data.data);
        setIsInitialized(data.data.orchestrator_status === 'running');
      } else {
        setError(data.error);
      }
    } catch (error) {
      console.error('시스템 상태 확인 실패:', error);
      setError('시스템 상태를 확인할 수 없습니다.');
    }
  };

  const initializeAgents = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/agents/initialize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          base_url: 'http://localhost:1234/v1',
          model_name: 'local-model',
          max_tokens: 2000,
          temperature: 0.7
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setIsInitialized(true);
        await checkSystemStatus();
      } else {
        setError(data.error);
      }
    } catch (error) {
      console.error('에이전트 초기화 실패:', error);
      setError('AI 에이전트 초기화에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/agents/test/connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          base_url: 'http://localhost:1234/v1',
          model_name: 'local-model'
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('LM Studio 연결 성공!\n사용 가능한 모델: ' + data.data.available_models.join(', '));
      } else {
        setError('LM Studio 연결 실패: ' + data.error);
      }
    } catch (error) {
      setError('연결 테스트 실패: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'status', label: '시스템 상태', icon: '🔧' },
    { id: 'analysis', label: '논문 분석', icon: '📄' },
    { id: 'discovery', label: '연구 발견', icon: '🔍' },
    { id: 'citation', label: '인용 네트워크', icon: '🕸️' }
  ];

  return (
    <div className="agents-container">
      <div className="agents-header">
        <h1 className="agents-title">
          🤖 AI Research Agents
        </h1>
        <p className="agents-subtitle">
          LM Studio 기반 AI 연구 어시스턴트 시스템
        </p>
      </div>

      <div className="status-panel">
        <h3>📊 시스템 상태</h3>
        <div className="status-grid">
          <div className="status-item">
            <div className="status-value">
              {systemStatus.orchestrator_status === 'running' ? '✅' : '❌'}
            </div>
            <div className="status-label">오케스트레이터</div>
          </div>
          <div className="status-item">
            <div className="status-value">
              {systemStatus.llm_connection ? '✅' : '❌'}
            </div>
            <div className="status-label">LM Studio</div>
          </div>
          <div className="status-item">
            <div className="status-value">
              {Object.keys(systemStatus.agents || {}).length}
            </div>
            <div className="status-label">활성 에이전트</div>
          </div>
          <div className="status-item">
            <div className="status-value">
              {systemStatus.active_workflows || 0}
            </div>
            <div className="status-label">실행중 워크플로</div>
          </div>
        </div>
        
        <div style={{ marginTop: '15px' }}>
          {!isInitialized && (
            <button 
              className="btn-primary" 
              onClick={initializeAgents}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <div className="loading-spinner"></div>
                  초기화 중...
                </>
              ) : (
                '🚀 AI 에이전트 초기화'
              )}
            </button>
          )}
          
          <button 
            className="btn-secondary" 
            onClick={testConnection}
            disabled={isLoading}
            style={{ marginLeft: '10px' }}
          >
            🔌 LM Studio 연결 테스트
          </button>
          
          <button 
            className="btn-secondary" 
            onClick={checkSystemStatus}
            disabled={isLoading}
            style={{ marginLeft: '10px' }}
          >
            🔄 상태 새로고침
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {!isInitialized && !error && (
        <div className="warning-message">
          ⚠️ AI 에이전트가 초기화되지 않았습니다. 먼저 LM Studio가 실행 중인지 확인하고 초기화 버튼을 클릭하세요.
        </div>
      )}

      {isInitialized && (
        <>
          <div className="agent-tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>

          <div className="tab-content">
            {activeTab === 'status' && (
              <SystemStatusPanel 
                systemStatus={systemStatus} 
                onRefresh={checkSystemStatus}
              />
            )}
            
            {activeTab === 'analysis' && (
              <PaperAnalysisPanel />
            )}
            
            {activeTab === 'discovery' && (
              <ResearchDiscoveryPanel />
            )}
            
            {activeTab === 'citation' && (
              <CitationNetworkPanel />
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ResearchAgents;