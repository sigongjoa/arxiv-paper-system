import React, { useState, useEffect } from 'react';

const SystemStatusPanel = ({ systemStatus, onRefresh }) => {
  const [detailedStats, setDetailedStats] = useState(null);
  const [recentWorkflows, setRecentWorkflows] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (systemStatus.orchestrator_status === 'running') {
      loadDetailedStats();
    }
  }, [systemStatus]);

  const loadDetailedStats = async () => {
    setIsLoading(true);
    try {
      setTimeout(() => {
        setDetailedStats({
          total_analyses: 47,
          total_workflows: 23,
          completed_workflows: 21,
          average_execution_time: 45.2,
          success_rate: 91.3,
          total_papers_analyzed: 156,
          total_recommendations_generated: 342,
          active_agents: 3
        });
        
        setRecentWorkflows([
          {
            workflow_id: 'comprehensive_001',
            workflow_type: 'comprehensive',
            status: 'completed',
            execution_time: 34.5,
            created_at: '2025-01-15 14:30:22'
          },
          {
            workflow_id: 'single_paper_002',
            workflow_type: 'single_paper',
            status: 'completed',
            execution_time: 12.3,
            created_at: '2025-01-15 14:25:10'
          },
          {
            workflow_id: 'research_discovery_003',
            workflow_type: 'discovery',
            status: 'running',
            execution_time: null,
            created_at: '2025-01-15 14:28:45'
          }
        ]);
        
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      setError('상세 통계 로드 실패: ' + error.message);
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return '🟢';
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'pending': return '⏳';
      default: return '❓';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return '#4caf50';
      case 'completed': return '#2196f3';
      case 'failed': return '#f44336';
      case 'pending': return '#ff9800';
      default: return '#666';
    }
  };

  const formatExecutionTime = (seconds) => {
    if (!seconds) return 'N/A';
    return seconds < 60 ? `${seconds.toFixed(1)}초` : `${(seconds / 60).toFixed(1)}분`;
  };

  return (
    <div className="agent-panel">
      <h2 className="panel-title">
        <span className="panel-icon">📊</span>
        시스템 상태 및 통계
      </h2>
      
      <p>AI 연구 에이전트 시스템의 상태와 성능 지표를 확인합니다.</p>

      <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h3>🔧 시스템 컴포넌트 상태</h3>
        
        <div className="status-grid">
          <div className="status-item">
            <div className="status-value" style={{ color: systemStatus.orchestrator_status === 'running' ? '#4caf50' : '#f44336' }}>
              {systemStatus.orchestrator_status === 'running' ? '🟢 실행중' : '🔴 중지됨'}
            </div>
            <div className="status-label">오케스트레이터</div>
          </div>
          
          <div className="status-item">
            <div className="status-value" style={{ color: systemStatus.llm_connection ? '#4caf50' : '#f44336' }}>
              {systemStatus.llm_connection ? '🟢 연결됨' : '🔴 연결안됨'}
            </div>
            <div className="status-label">LM Studio 연결</div>
          </div>
          
          <div className="status-item">
            <div className="status-value">
              {Object.keys(systemStatus.agents || {}).length}
            </div>
            <div className="status-label">활성 에이전트</div>
          </div>
          
          <div className="status-item">
            <div className="status-value">
              {systemStatus.available_models?.length || 0}
            </div>
            <div className="status-label">사용 가능한 모델</div>
          </div>
        </div>

        {systemStatus.agents && Object.keys(systemStatus.agents).length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <h4>🤖 에이전트 상세 상태</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '10px' }}>
              {Object.entries(systemStatus.agents).map(([agentName, agentStatus]) => (
                <div 
                  key={agentName}
                  style={{
                    background: 'white',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    padding: '12px'
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                    {agentName.replace('Agent', '')}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>
                    상태: {agentStatus.status || 'ready'}
                  </div>
                  {agentStatus.total_papers && (
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>
                      처리 논문: {agentStatus.total_papers}개
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {detailedStats && (
        <div style={{ marginBottom: '20px' }}>
          <h3>📈 성능 통계</h3>
          
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-value">
                {detailedStats.total_analyses}
              </div>
              <div className="metric-label">총 분석 수행</div>
            </div>
            
            <div className="metric-card">
              <div className="metric-value">
                {detailedStats.success_rate.toFixed(1)}%
              </div>
              <div className="metric-label">성공률</div>
            </div>
            
            <div className="metric-card">
              <div className="metric-value">
                {detailedStats.average_execution_time.toFixed(1)}초
              </div>
              <div className="metric-label">평균 실행 시간</div>
            </div>
            
            <div className="metric-card">
              <div className="metric-value">
                {detailedStats.total_papers_analyzed}
              </div>
              <div className="metric-label">분석된 논문</div>
            </div>
          </div>
        </div>
      )}

      {recentWorkflows.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3>🔄 최근 워크플로</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {recentWorkflows.map((workflow, index) => (
              <div 
                key={index}
                style={{
                  background: 'white',
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px',
                  padding: '15px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                    {getStatusIcon(workflow.status)} {workflow.workflow_id}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>
                    유형: {workflow.workflow_type} | 시작: {workflow.created_at}
                  </div>
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div 
                    style={{
                      color: getStatusColor(workflow.status),
                      fontWeight: 'bold',
                      marginBottom: '5px'
                    }}
                  >
                    {workflow.status.toUpperCase()}
                  </div>
                  {workflow.execution_time && (
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>
                      실행시간: {formatExecutionTime(workflow.execution_time)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px' }}>
        <button 
          className="btn-primary" 
          onClick={() => {
            onRefresh();
            loadDetailedStats();
          }}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <div className="loading-spinner"></div>
              로딩 중...
            </>
          ) : (
            '🔄 상태 새로고침'
          )}
        </button>
        
        <button className="btn-secondary">
          📋 상세 로그 보기
        </button>
      </div>

      {error && (
        <div className="error-message" style={{ marginTop: '15px' }}>
          ❌ {error}
        </div>
      )}
    </div>
  );
};

export default SystemStatusPanel;