import React, { useState } from 'react';

const CitationNetworkPanel = () => {
  const [papers, setPapers] = useState([]);
  const [networkAnalysis, setNetworkAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [newPaper, setNewPaper] = useState({
    id: '',
    title: '',
    content: ''
  });

  const addPaper = () => {
    if (!newPaper.id.trim() || !newPaper.title.trim()) {
      setError('논문 ID와 제목은 필수입니다.');
      return;
    }

    const paper = {
      id: newPaper.id,
      title: newPaper.title,
      content: newPaper.content || `This is a research paper titled "${newPaper.title}". The paper discusses various aspects of the research topic.`,
      authors: ['Sample Author'],
      abstract: 'Sample abstract for the paper.'
    };

    setPapers(prev => [...prev, paper]);
    setNewPaper({ id: '', title: '', content: '' });
    setError(null);
  };

  const removePaper = (index) => {
    setPapers(prev => prev.filter((_, i) => i !== index));
  };

  const analyzeNetwork = async () => {
    if (papers.length < 2) {
      setError('인용 네트워크 분석을 위해서는 최소 2개의 논문이 필요합니다.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setNetworkAnalysis(null);

    try {
      const response = await fetch('/api/agents/analyze/citation-network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(papers)
      });

      const data = await response.json();

      if (data.success) {
        setNetworkAnalysis(data.data.network_analysis);
      } else {
        setError(data.error || '인용 네트워크 분석에 실패했습니다.');
      }
    } catch (error) {
      console.error('인용 네트워크 분석 실패:', error);
      setError('서버 연결에 실패했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadSamplePapers = () => {
    const samplePapers = [
      {
        id: 'paper_001',
        title: 'Attention Is All You Need',
        content: 'This paper introduces the Transformer architecture. The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
        authors: ['Vaswani et al.'],
        abstract: 'We propose the Transformer, a model architecture based solely on attention mechanisms.'
      },
      {
        id: 'paper_002',
        title: 'BERT: Pre-training of Deep Bidirectional Transformers',
        content: 'We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers. BERT is designed to pre-train deep bidirectional representations by jointly conditioning on both left and right context. This work builds upon the Transformer architecture (Vaswani et al.).',
        authors: ['Devlin et al.'],
        abstract: 'BERT obtains new state-of-the-art results on eleven natural language processing tasks.'
      },
      {
        id: 'paper_003',
        title: 'GPT-3: Language Models are Few-Shot Learners',
        content: 'We train GPT-3, an autoregressive language model with 175 billion parameters. GPT-3 achieves strong performance on many NLP datasets. Like BERT (Devlin et al.), this model is based on the Transformer architecture.',
        authors: ['Brown et al.'],
        abstract: 'GPT-3 demonstrates that scaling up language models greatly improves task-agnostic, few-shot performance.'
      }
    ];
    
    setPapers(samplePapers);
  };

  return (
    <div className="agent-panel">
      <h2 className="panel-title">
        <span className="panel-icon">🕸️</span>
        인용 네트워크 분석 에이전트
      </h2>
      
      <p>논문 간의 인용 관계를 분석하여 연구 네트워크와 영향력을 파악합니다.</p>

      <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h3>📚 논문 추가</h3>
        
        <div className="form-group">
          <label className="form-label">논문 ID *</label>
          <input
            type="text"
            className="form-input"
            value={newPaper.id}
            onChange={(e) => setNewPaper(prev => ({ ...prev, id: e.target.value }))}
            placeholder="예: arxiv:2023.12345"
          />
        </div>

        <div className="form-group">
          <label className="form-label">논문 제목 *</label>
          <input
            type="text"
            className="form-input"
            value={newPaper.title}
            onChange={(e) => setNewPaper(prev => ({ ...prev, title: e.target.value }))}
            placeholder="논문 제목을 입력하세요"
          />
        </div>

        <div className="form-group">
          <label className="form-label">논문 내용 (선택)</label>
          <textarea
            className="form-textarea"
            value={newPaper.content}
            onChange={(e) => setNewPaper(prev => ({ ...prev, content: e.target.value }))}
            placeholder="논문 내용을 입력하면 더 정확한 인용 분석이 가능합니다"
            style={{ minHeight: '80px' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-primary" onClick={addPaper}>
            ➕ 논문 추가
          </button>
          <button className="btn-secondary" onClick={loadSamplePapers}>
            📝 샘플 논문 로드
          </button>
        </div>
      </div>

      {papers.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3>📋 분석 대상 논문 ({papers.length}개)</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {papers.map((paper, index) => (
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
                    {paper.title}
                  </div>
                  <div style={{ color: '#666', fontSize: '0.9rem' }}>
                    ID: {paper.id}
                  </div>
                </div>
                <button 
                  className="btn-secondary"
                  onClick={() => removePaper(index)}
                  style={{ padding: '5px 10px', fontSize: '0.8rem' }}
                >
                  🗑️ 제거
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <button 
          className="btn-primary" 
          onClick={analyzeNetwork}
          disabled={isAnalyzing || papers.length < 2}
        >
          {isAnalyzing ? (
            <>
              <div className="loading-spinner"></div>
              네트워크 분석 중...
            </>
          ) : (
            '🕸️ 인용 네트워크 분석'
          )}
        </button>
        
        {papers.length < 2 && (
          <div style={{ marginTop: '10px', fontSize: '0.9rem', color: '#666' }}>
            💡 분석을 위해 최소 2개의 논문을 추가하세요.
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {networkAnalysis && (
        <div className="result-panel">
          <h3 className="result-title">📊 인용 네트워크 분석 결과</h3>
          
          {networkAnalysis.network_metrics && (
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-value">
                  {networkAnalysis.network_metrics.total_nodes || 0}
                </div>
                <div className="metric-label">총 논문 수</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {networkAnalysis.network_metrics.total_edges || 0}
                </div>
                <div className="metric-label">인용 관계 수</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {(networkAnalysis.network_metrics.density * 100).toFixed(1)}%
                </div>
                <div className="metric-label">네트워크 밀도</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {networkAnalysis.network_metrics.average_clustering?.toFixed(3) || '0.000'}
                </div>
                <div className="metric-label">클러스터링 계수</div>
              </div>
            </div>
          )}

          {networkAnalysis.influential_papers && networkAnalysis.influential_papers.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4>🏆 영향력 있는 논문</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {networkAnalysis.influential_papers.slice(0, 5).map((paper, index) => (
                  <div 
                    key={index}
                    style={{
                      background: 'white',
                      border: '1px solid #e0e0e0',
                      borderRadius: '8px',
                      padding: '15px'
                    }}
                  >
                    <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                      #{index + 1} {paper.title || paper.id}
                    </div>
                    
                    {paper.influence_metrics && (
                      <div style={{ display: 'flex', gap: '15px', fontSize: '0.9rem', color: '#666' }}>
                        <span>PageRank: {(paper.influence_metrics.pagerank * 100).toFixed(2)}%</span>
                        <span>인용 수: {paper.influence_metrics.citation_count || 0}</span>
                        <span>종합 점수: {(paper.influence_metrics.combined_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginTop: '20px', padding: '15px', background: '#e3f2fd', borderRadius: '8px', fontSize: '0.9rem' }}>
            💡 <strong>분석 설명:</strong><br/>
            • <strong>PageRank:</strong> 논문의 전체적인 영향력을 나타냅니다<br/>
            • <strong>인용 수:</strong> 해당 논문을 인용한 다른 논문의 수입니다<br/>
            • <strong>네트워크 밀도:</strong> 전체 가능한 연결 중 실제 연결의 비율입니다<br/>
            • <strong>클러스터:</strong> 유사한 연구 주제의 논문들이 그룹화된 것입니다
          </div>
        </div>
      )}
    </div>
  );
};

export default CitationNetworkPanel;