import React, { useState } from 'react';

const ResearchDiscoveryPanel = () => {
  const [queryText, setQueryText] = useState('');
  const [researchInterests, setResearchInterests] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [recommendations, setRecommendations] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);

  const discoverResearch = async () => {
    if (!queryText.trim()) {
      setError('검색 쿼리를 입력해주세요.');
      return;
    }

    setIsSearching(true);
    setError(null);
    setRecommendations([]);

    try {
      const requestData = {
        query_text: queryText,
        research_interests: researchInterests.split(',').map(i => i.trim()).filter(i => i),
        max_results: maxResults,
        exclude_papers: []
      };

      const response = await fetch('/api/agents/discover/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (data.success) {
        setRecommendations(data.data.recommendations || []);
        if (data.data.recommendations?.length === 0) {
          setError('검색 결과가 없습니다. 다른 키워드로 시도해보세요.');
        }
      } else {
        setError(data.error || '연구 발견에 실패했습니다.');
      }
    } catch (error) {
      console.error('연구 발견 실패:', error);
      setError('서버 연결에 실패했습니다.');
    } finally {
      setIsSearching(false);
    }
  };

  const loadSampleQuery = () => {
    setQueryText('transformer 기반 자연어 처리 모델의 최신 연구 동향');
    setResearchInterests('자연어처리, 딥러닝, 어텐션 메커니즘, 기계번역');
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return '#4caf50';
    if (score >= 0.6) return '#ff9800';
    return '#f44336';
  };

  const getScoreLabel = (score) => {
    if (score >= 0.8) return '높음';
    if (score >= 0.6) return '보통';
    return '낮음';
  };

  return (
    <div className="agent-panel">
      <h2 className="panel-title">
        <span className="panel-icon">🔍</span>
        연구 발견 에이전트
      </h2>
      
      <p>시맨틱 검색을 통해 관련 연구 논문을 발견하고 추천합니다.</p>

      <div className="form-group">
        <label className="form-label">연구 쿼리 *</label>
        <textarea
          className="form-textarea"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          placeholder="찾고 싶은 연구 주제나 키워드를 자세히 입력하세요"
          style={{ minHeight: '100px' }}
        />
      </div>

      <div className="form-group">
        <label className="form-label">연구 관심사 (쉼표로 구분)</label>
        <input
          type="text"
          className="form-input"
          value={researchInterests}
          onChange={(e) => setResearchInterests(e.target.value)}
          placeholder="머신러닝, 자연어처리, 컴퓨터비전, 딥러닝"
        />
      </div>

      <div className="form-group">
        <label className="form-label">최대 결과 수</label>
        <select
          className="form-select"
          value={maxResults}
          onChange={(e) => setMaxResults(parseInt(e.target.value))}
        >
          <option value={5}>5개</option>
          <option value={10}>10개</option>
          <option value={20}>20개</option>
          <option value={50}>50개</option>
        </select>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button 
          className="btn-primary" 
          onClick={discoverResearch}
          disabled={isSearching}
        >
          {isSearching ? (
            <>
              <div className="loading-spinner"></div>
              검색 중...
            </>
          ) : (
            '🔍 연구 발견 시작'
          )}
        </button>
        
        <button 
          className="btn-secondary" 
          onClick={loadSampleQuery}
          disabled={isSearching}
        >
          📝 샘플 쿼리 로드
        </button>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {isSearching && (
        <div className="warning-message">
          🔄 AI가 관련 연구를 검색하고 있습니다. 잠시만 기다려주세요...
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="result-panel">
          <h3 className="result-title">
            📊 발견된 연구 ({recommendations.length}개)
          </h3>
          
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-value">
                {recommendations.length}
              </div>
              <div className="metric-label">총 추천 논문</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {(recommendations.reduce((sum, rec) => sum + rec.relevance_score, 0) / recommendations.length).toFixed(2)}
              </div>
              <div className="metric-label">평균 관련성</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {recommendations.filter(rec => rec.relevance_score >= 0.8).length}
              </div>
              <div className="metric-label">고관련성 논문</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {Math.max(...recommendations.map(rec => rec.relevance_score)).toFixed(2)}
              </div>
              <div className="metric-label">최고 관련성</div>
            </div>
          </div>

          <div className="recommendation-list">
            {recommendations.map((rec, index) => (
              <div key={index} className="recommendation-item">
                <div className="recommendation-title">
                  #{index + 1} {rec.title || `논문 ${rec.paper_id}`}
                </div>
                
                <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
                  <span 
                    className="recommendation-score"
                    style={{ backgroundColor: getScoreColor(rec.relevance_score) + '20', color: getScoreColor(rec.relevance_score) }}
                  >
                    관련성: {(rec.relevance_score * 100).toFixed(1)}% ({getScoreLabel(rec.relevance_score)})
                  </span>
                  
                  {rec.semantic_similarity && (
                    <span 
                      style={{
                        background: '#f3e5f5',
                        color: '#7b1fa2',
                        padding: '4px 12px',
                        borderRadius: '20px',
                        fontSize: '0.85rem',
                        fontWeight: '500',
                        display: 'inline-block'
                      }}
                    >
                      유사도: {(rec.semantic_similarity * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                
                {rec.reason && (
                  <div className="recommendation-reason">
                    <strong>추천 이유:</strong> {rec.reason}
                  </div>
                )}
                
                <div style={{ marginTop: '10px', fontSize: '0.9rem', color: '#888' }}>
                  📄 논문 ID: {rec.paper_id}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '20px', padding: '15px', background: '#e8f5e8', borderRadius: '8px', fontSize: '0.9rem' }}>
            💡 <strong>팁:</strong> 더 정확한 결과를 원한다면 구체적인 키워드와 연구 분야를 입력해보세요. 
            관련성 점수가 높을수록 검색 쿼리와 더 유사한 연구입니다.
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchDiscoveryPanel;