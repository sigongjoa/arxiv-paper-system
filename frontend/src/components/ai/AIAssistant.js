import React, { useState, useEffect } from 'react';
import './AIAssistant.css';

const AIAssistant = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [selectedPaper, setSelectedPaper] = useState('');
  const [analysisType, setAnalysisType] = useState('comprehensive');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [recentPapers, setRecentPapers] = useState([]);

  useEffect(() => {
    checkSystemStatus();
    loadRecentPapers();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('/api/enhanced/ai/enhanced/models/status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to get system status:', error);
      setSystemStatus({ error: 'Failed to connect to AI system' });
    }
  };

  const loadRecentPapers = async () => {
    try {
      const response = await fetch('/api/papers?limit=20');
      const papers = await response.json();
      setRecentPapers(papers.slice(0, 10));
    } catch (error) {
      console.error('Failed to load papers:', error);
    }
  };

  const runAnalysis = async () => {
    if (!selectedPaper) {
      alert('논문을 선택해주세요.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      let endpoint = '';
      switch (analysisType) {
        case 'comprehensive':
          endpoint = '/api/enhanced/ai/enhanced/comprehensive';
          break;
        case 'methodology':
          endpoint = '/api/ai/extract/findings';
          break;
        case 'quality':
          endpoint = '/api/ai/assess/quality';
          break;
        case 'research_gaps':
          endpoint = '/api/enhanced/ai/enhanced/research-gaps';
          break;
        default:
          endpoint = '/api/ai/analyze/comprehensive';
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ arxiv_id: selectedPaper })
      });

      const result = await response.json();
      setAnalysisResult(result);
      
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysisResult({ error: 'Analysis failed: ' + error.message });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const saveToNotion = async () => {
    if (!analysisResult || !selectedPaper) return;

    try {
      const response = await fetch('/api/enhanced/save-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          arxiv_id: selectedPaper,
          analysis_data: analysisResult,
          analysis_type: analysisType
        })
      });

      const result = await response.json();
      if (result.success) {
        alert('분석 결과가 Notion에 저장되었습니다!');
      } else {
        alert('저장 실패: ' + result.error);
      }
    } catch (error) {
      console.error('Save to Notion failed:', error);
      alert('저장 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="ai-assistant">
      <div className="assistant-header">
        <h2>🤖 AI Research Assistant</h2>
        <p>Advanced paper analysis with LM Studio integration</p>
      </div>

      <div className="assistant-grid">
        {/* System Status Panel */}
        <div className="panel system-status">
          <h3>📊 System Status</h3>
          {systemStatus ? (
            systemStatus.error ? (
              <div className="status-error">
                <p>❌ {systemStatus.error}</p>
                <button onClick={checkSystemStatus} className="retry-btn">
                  Retry Connection
                </button>
              </div>
            ) : (
              <div className="status-grid">
                <div className="status-item">
                  <span className="status-label">LM Studio</span>
                  <span className={`status-value ${systemStatus.health?.status === 'healthy' ? 'healthy' : 'error'}`}>
                    {systemStatus.health?.status || 'Unknown'}
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">Available Models</span>
                  <span className="status-value">
                    {systemStatus.health?.available_models?.length || 0}
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">Performance</span>
                  <span className="status-value healthy">Optimal</span>
                </div>
              </div>
            )
          ) : (
            <div className="loading">Checking system status...</div>
          )}
        </div>

        {/* Quick Analysis Panel */}
        <div className="panel quick-analysis">
          <h3>⚡ Quick Analysis</h3>
          
          <div className="analysis-form">
            <div className="form-group">
              <label>Select Paper:</label>
              <select 
                value={selectedPaper} 
                onChange={(e) => setSelectedPaper(e.target.value)}
                className="paper-select"
              >
                <option value="">Choose a paper...</option>
                {recentPapers.map(paper => (
                  <option key={paper.arxiv_id} value={paper.arxiv_id}>
                    {paper.arxiv_id} - {paper.title.substring(0, 60)}...
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Analysis Type:</label>
              <select 
                value={analysisType} 
                onChange={(e) => setAnalysisType(e.target.value)}
                className="analysis-select"
              >
                <option value="comprehensive">🔍 Comprehensive Analysis</option>
                <option value="methodology">🔬 Methodology Details</option>
                <option value="quality">⭐ Quality Assessment</option>
                <option value="research_gaps">🎯 Research Gaps</option>
              </select>
            </div>

            <div className="form-actions">
              <button 
                onClick={runAnalysis}
                disabled={isAnalyzing || !selectedPaper}
                className="analyze-btn primary"
              >
                {isAnalyzing ? '🔄 Analyzing...' : '🚀 Run Analysis'}
              </button>
              
              {analysisResult && !analysisResult.error && (
                <button onClick={saveToNotion} className="save-btn">
                  💾 Save to Notion
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Analysis Results Panel */}
        <div className="panel analysis-results">
          <h3>📋 Analysis Results</h3>
          
          {isAnalyzing && (
            <div className="loading-analysis">
              <div className="loading-spinner"></div>
              <p>AI is analyzing the paper...</p>
            </div>
          )}

          {analysisResult && (
            <div className="results-content">
              {analysisResult.error ? (
                <div className="error-result">
                  <p>❌ {analysisResult.error}</p>
                </div>
              ) : (
                <div className="success-result">
                  <AnalysisDisplay result={analysisResult} type={analysisType} />
                </div>
              )}
            </div>
          )}

          {!isAnalyzing && !analysisResult && (
            <div className="no-results">
              <p>Select a paper and run analysis to see results here.</p>
            </div>
          )}
        </div>

        {/* Quick Actions Panel */}
        <div className="panel quick-actions">
          <h3>🛠️ Quick Actions</h3>
          
          <div className="action-grid">
            <button className="action-btn" onClick={() => window.open('/api/health', '_blank')}>
              🔍 System Diagnostics
            </button>
            
            <button className="action-btn" onClick={loadRecentPapers}>
              🔄 Refresh Papers
            </button>
            
            <button className="action-btn" onClick={checkSystemStatus}>
              📡 Check AI Status
            </button>
            
            <button className="action-btn" onClick={() => setAnalysisResult(null)}>
              🗑️ Clear Results
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const AnalysisDisplay = ({ result, type }) => {
  const renderContent = () => {
    switch (type) {
      case 'comprehensive':
        return (
          <div className="comprehensive-display">
            {result.comprehensive_analysis?.background && (
              <div className="analysis-section">
                <h4>🎯 Research Background</h4>
                <p><strong>Problem:</strong> {result.comprehensive_analysis.background.problem_definition}</p>
                <p><strong>Motivation:</strong> {result.comprehensive_analysis.background.motivation}</p>
              </div>
            )}
            
            {result.comprehensive_analysis?.quality_scores && (
              <div className="analysis-section">
                <h4>⭐ Quality Scores</h4>
                <div className="scores-grid">
                  {Object.entries(result.comprehensive_analysis.quality_scores).map(([key, value]) => (
                    typeof value === 'number' && (
                      <div key={key} className="score-item">
                        <span>{key}:</span>
                        <span className="score-value">{value}/100</span>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'research_gaps':
        return (
          <div className="gaps-display">
            {result.identified_gaps && (
              <div className="analysis-section">
                <h4>🔍 Identified Research Gaps</h4>
                {Object.entries(result.identified_gaps).map(([category, gaps]) => (
                  <div key={category} className="gap-category">
                    <h5>{category}:</h5>
                    <ul>
                      {gaps.slice(0, 3).map((gap, idx) => (
                        <li key={idx}>{gap}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="generic-display">
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        );
    }
  };

  return (
    <div className="analysis-display">
      <div className="analysis-meta">
        <span className="analysis-type-badge">{type}</span>
        <span className="analysis-time">
          {result.analysis_timestamp && new Date(result.analysis_timestamp).toLocaleString()}
        </span>
      </div>
      {renderContent()}
    </div>
  );
};

export default AIAssistant;
