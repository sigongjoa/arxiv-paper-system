import React, { useState, useEffect } from 'react';
import '../styles/common.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const RecommendationSystem = () => {
  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [recommendationType, setRecommendationType] = useState('hybrid');
  const [initializationStatus, setInitializationStatus] = useState('');

  useEffect(() => {
    loadPapers();
    checkSystemStatus();
  }, []);

  const loadPapers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/papers?limit=100`);
      const data = await response.json();
      setPapers(data);
    } catch (error) {
      console.error('논문 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/recommendations/status`);
      const status = await response.json();
      setSystemStatus(status);
    } catch (error) {
      console.error('시스템 상태 확인 실패:', error);
    }
  };

  const initializeSystem = async () => {
    try {
      setInitializationStatus('초기화 중...');
      const response = await fetch(`${API_BASE_URL}/recommendations/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_rebuild: false })
      });
      const result = await response.json();
      
      if (result.success) {
        setInitializationStatus('초기화 완료');
        checkSystemStatus();
      } else {
        setInitializationStatus(`초기화 실패: ${result.error}`);
      }
    } catch (error) {
      console.error('시스템 초기화 실패:', error);
      setInitializationStatus(`초기화 실패: ${error.message}`);
    }
  };

  const getRecommendations = async (paperId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/recommendations/get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_id: paperId,
          type: recommendationType,
          n_recommendations: 10
        })
      });
      const result = await response.json();
      
      if (result.error) {
        if (result.initialization_required) {
          setInitializationStatus('시스템 초기화가 필요합니다');
        }
        console.error('추천 생성 실패:', result.error);
        setRecommendations([]);
      } else {
        setRecommendations(result.recommendations || []);
      }
    } catch (error) {
      console.error('추천 요청 실패:', error);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePaperSelect = (paper) => {
    setSelectedPaper(paper);
    getRecommendations(paper.arxiv_id);
  };

  const filteredPapers = papers.filter(paper =>
    paper.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    paper.abstract.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  const truncateText = (text, maxLength) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="RecommendationContainer">
      <div className="PageHeader">
        <h2>논문 추천 시스템</h2>
        <div className="SystemStatus">
          {systemStatus && (
            <div className={`StatusBadge ${systemStatus.initialized ? 'success' : 'warning'}`}>
              {systemStatus.initialized ? '시스템 준비됨' : '시스템 초기화 필요'}
              {systemStatus.paper_count > 0 && ` (${systemStatus.paper_count}개 논문)`}
            </div>
          )}
        </div>
      </div>

      {!systemStatus?.initialized && (
        <div className="InitializationPanel">
          <div className="Alert warning">
            <h3>추천 시스템 초기화 필요</h3>
            <p>논문 추천을 위해 시스템을 먼저 초기화해야 합니다. 이 과정은 몇 분 정도 소요될 수 있습니다.</p>
            <button 
              className="PrimaryButton" 
              onClick={initializeSystem}
              disabled={initializationStatus.includes('중')}
            >
              {initializationStatus.includes('중') ? '초기화 진행 중...' : '시스템 초기화'}
            </button>
            {initializationStatus && (
              <div className="StatusMessage">{initializationStatus}</div>
            )}
          </div>
        </div>
      )}

      <div className="ContentLayout">
        {/* 논문 선택 영역 */}
        <div className="PaperSelectionPanel">
          <div className="PanelHeader">
            <h3>논문 선택</h3>
            <div className="SearchBox">
              <input
                type="text"
                placeholder="논문 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="SearchInput"
              />
            </div>
          </div>

          <div className="RecommendationSettings">
            <label>
              추천 방식:
              <select 
                value={recommendationType} 
                onChange={(e) => setRecommendationType(e.target.value)}
                className="SelectInput"
              >
                <option value="hybrid">하이브리드 추천</option>
                <option value="content">콘텐츠 기반</option>
              </select>
            </label>
          </div>

          <div className="PaperList">
            {loading && !selectedPaper ? (
              <div className="LoadingSpinner">논문 로딩 중...</div>
            ) : (
              filteredPapers.slice(0, 20).map(paper => (
                <div 
                  key={paper.arxiv_id} 
                  className={`PaperCard ${selectedPaper?.arxiv_id === paper.arxiv_id ? 'selected' : ''}`}
                  onClick={() => handlePaperSelect(paper)}
                >
                  <div className="PaperTitle">{truncateText(paper.title, 100)}</div>
                  <div className="PaperMeta">
                    <span className="ArxivId">{paper.arxiv_id}</span>
                    <span className="PublishDate">{formatDate(paper.published_date)}</span>
                  </div>
                  <div className="Categories">
                    {paper.categories.slice(0, 3).map(cat => (
                      <span key={cat} className="CategoryTag">{cat}</span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 추천 결과 영역 */}
        <div className="RecommendationPanel">
          {selectedPaper && (
            <>
              <div className="SelectedPaperInfo">
                <h3>선택된 논문</h3>
                <div className="SelectedPaper">
                  <div className="PaperTitle">{selectedPaper.title}</div>
                  <div className="PaperMeta">
                    <span className="ArxivId">{selectedPaper.arxiv_id}</span>
                    <span className="PublishDate">{formatDate(selectedPaper.published_date)}</span>
                  </div>
                  <div className="PaperAbstract">
                    {truncateText(selectedPaper.abstract, 200)}
                  </div>
                </div>
              </div>

              <div className="RecommendationResults">
                <h3>추천 논문 ({recommendations.length}개)</h3>
                
                {loading ? (
                  <div className="LoadingSpinner">추천 생성 중...</div>
                ) : recommendations.length > 0 ? (
                  <div className="RecommendationList">
                    {recommendations.map((rec, index) => (
                      <div key={rec.arxiv_id} className="RecommendationCard">
                        <div className="RankBadge">#{index + 1}</div>
                        <div className="RecommendationContent">
                          <div className="PaperTitle">
                            <a 
                              href={rec.pdf_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="TitleLink"
                            >
                              {rec.title}
                            </a>
                          </div>
                          <div className="PaperMeta">
                            <span className="ArxivId">{rec.arxiv_id}</span>
                            <span className="PublishDate">{formatDate(rec.published_date)}</span>
                          </div>
                          <div className="Categories">
                            {rec.categories.slice(0, 3).map(cat => (
                              <span key={cat} className="CategoryTag">{cat}</span>
                            ))}
                          </div>
                          <div className="PaperAbstract">
                            {truncateText(rec.abstract, 150)}
                          </div>
                          <div className="ScoreInfo">
                            {rec.similarity_score && (
                              <span className="SimilarityScore">
                                의미 유사도: {(rec.similarity_score * 100).toFixed(1)}%
                              </span>
                            )}
                            {rec.hybrid_score && (
                              <span className="HybridScore">
                                종합 점수: {rec.hybrid_score.toFixed(3)}
                              </span>
                            )}
                            {rec.semantic_score && rec.cluster_score && (
                              <span className="DetailedScores">
                                의미: {rec.semantic_score.toFixed(3)} | 주제: {rec.cluster_score.toFixed(3)}
                              </span>
                            )}
                            {rec.methods && (
                              <span className="Methods">
                                방법: {rec.methods.join(' + ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="NoRecommendations">
                    추천할 수 있는 논문이 없습니다.
                  </div>
                )}
              </div>
            </>
          )}

          {!selectedPaper && (
            <div className="EmptyState">
              <h3>논문을 선택하세요</h3>
              <p>왼쪽에서 논문을 선택하면 관련 논문을 추천해드립니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecommendationSystem;
