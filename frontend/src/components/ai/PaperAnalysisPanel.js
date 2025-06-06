import React, { useState } from 'react';

const PaperAnalysisPanel = () => {
  const [paperContent, setPaperContent] = useState('');
  const [paperMetadata, setPaperMetadata] = useState({
    id: '',
    title: '',
    authors: '',
    abstract: ''
  });
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const handleMetadataChange = (field, value) => {
    setPaperMetadata(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const analyzePaper = async () => {
    if (!paperContent.trim() || !paperMetadata.title.trim()) {
      setError('논문 내용과 제목은 필수입니다.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const requestData = {
        paper_content: paperContent,
        paper_metadata: {
          id: paperMetadata.id || `temp_${Date.now()}`,
          title: paperMetadata.title,
          authors: paperMetadata.authors.split(',').map(a => a.trim()).filter(a => a),
          abstract: paperMetadata.abstract
        }
      };

      const response = await fetch('/api/agents/analyze/paper', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (data.success) {
        setAnalysisResult(data.data);
      } else {
        setError(data.error || '논문 분석에 실패했습니다.');
      }
    } catch (error) {
      console.error('논문 분석 실패:', error);
      setError('서버 연결에 실패했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadSamplePaper = () => {
    setPaperMetadata({
      id: 'sample_001',
      title: 'Attention Is All You Need',
      authors: 'Ashish Vaswani, Noam Shazeer, Niki Parmar',
      abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder.'
    });
    
    setPaperContent(`Abstract: The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

Introduction: Recurrent neural networks, long short-term memory and gated recurrent neural networks in particular, have been firmly established as state of the art approaches in sequence modeling and transduction problems such as language modeling and machine translation.

Methodology: In this work, we present the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output.

Results: On two machine translation tasks, these models are superior in quality while being more parallelizable and requiring significantly less time to train.`);
  };

  return (
    <div className="agent-panel">
      <h2 className="panel-title">
        <span className="panel-icon">📄</span>
        논문 분석 에이전트
      </h2>
      
      <p>AI를 활용하여 논문의 핵심 내용을 구조화하고 분석합니다.</p>

      <div className="form-group">
        <label className="form-label">논문 제목 *</label>
        <input
          type="text"
          className="form-input"
          value={paperMetadata.title}
          onChange={(e) => handleMetadataChange('title', e.target.value)}
          placeholder="논문 제목을 입력하세요"
        />
      </div>

      <div className="form-group">
        <label className="form-label">저자 (쉼표로 구분)</label>
        <input
          type="text"
          className="form-input"
          value={paperMetadata.authors}
          onChange={(e) => handleMetadataChange('authors', e.target.value)}
          placeholder="저자1, 저자2, 저자3"
        />
      </div>

      <div className="form-group">
        <label className="form-label">초록</label>
        <textarea
          className="form-textarea"
          value={paperMetadata.abstract}
          onChange={(e) => handleMetadataChange('abstract', e.target.value)}
          placeholder="논문 초록을 입력하세요"
          style={{ minHeight: '80px' }}
        />
      </div>

      <div className="form-group">
        <label className="form-label">논문 전체 내용 *</label>
        <textarea
          className="form-textarea"
          value={paperContent}
          onChange={(e) => setPaperContent(e.target.value)}
          placeholder="논문의 전체 텍스트를 입력하세요 (초록, 서론, 방법론, 결과, 결론 등)"
          style={{ minHeight: '200px' }}
        />
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button 
          className="btn-primary" 
          onClick={analyzePaper}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? (
            <>
              <div className="loading-spinner"></div>
              분석 중...
            </>
          ) : (
            '🔍 논문 분석 시작'
          )}
        </button>
        
        <button 
          className="btn-secondary" 
          onClick={loadSamplePaper}
          disabled={isAnalyzing}
        >
          📝 샘플 논문 로드
        </button>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {analysisResult && (
        <div className="result-panel">
          <h3 className="result-title">📊 분석 결과</h3>
          
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-value">
                {analysisResult.analysis.confidence_score?.toFixed(2) || '0.00'}
              </div>
              <div className="metric-label">신뢰도 점수</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {analysisResult.execution_time?.toFixed(1) || '0.0'}s
              </div>
              <div className="metric-label">분석 시간</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {analysisResult.analysis.key_insights?.length || 0}
              </div>
              <div className="metric-label">핵심 인사이트</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {analysisResult.analysis.technical_keywords?.length || 0}
              </div>
              <div className="metric-label">기술 키워드</div>
            </div>
          </div>

          {analysisResult.analysis.summary && (
            <div style={{ marginBottom: '20px' }}>
              <h4>📄 논문 요약</h4>
              <div className="result-content">
                {analysisResult.analysis.summary}
              </div>
            </div>
          )}

          {analysisResult.analysis.methodology && (
            <div style={{ marginBottom: '20px' }}>
              <h4>🔬 방법론</h4>
              <div className="result-content">
                {analysisResult.analysis.methodology}
              </div>
            </div>
          )}

          {analysisResult.analysis.main_findings && analysisResult.analysis.main_findings.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4>🎯 주요 발견사항</h4>
              <ul className="result-content">
                {analysisResult.analysis.main_findings.map((finding, index) => (
                  <li key={index} style={{ marginBottom: '8px' }}>
                    {finding}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {analysisResult.analysis.key_insights && analysisResult.analysis.key_insights.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4>💡 핵심 인사이트</h4>
              <ul className="result-content">
                {analysisResult.analysis.key_insights.map((insight, index) => (
                  <li key={index} style={{ marginBottom: '8px' }}>
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {analysisResult.analysis.technical_keywords && analysisResult.analysis.technical_keywords.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4>🏷️ 기술 키워드</h4>
              <div className="result-content">
                {analysisResult.analysis.technical_keywords.map((keyword, index) => (
                  <span 
                    key={index} 
                    style={{
                      display: 'inline-block',
                      background: '#e3f2fd',
                      color: '#1976d2',
                      padding: '4px 12px',
                      margin: '4px',
                      borderRadius: '16px',
                      fontSize: '0.9rem'
                    }}
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PaperAnalysisPanel;