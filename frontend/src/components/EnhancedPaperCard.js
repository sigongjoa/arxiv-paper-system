import React, { useState } from 'react';
import ChatBot from './ai/ChatBot';
import './EnhancedPaperCard.css';

const EnhancedPaperCard = ({ paper, onAnalyze, onCitationAnalysis, showDetails = false }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [showFullAbstract, setShowFullAbstract] = useState(false);
  const [isGeneratingShorts, setIsGeneratingShorts] = useState(false);

  const truncateText = (text, maxLength) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const handleQuickAnalysis = async (analysisType) => {
    setIsAnalyzing(true);
    try {
      let endpoint = '';
      switch (analysisType) {
        case 'comprehensive':
          endpoint = '/api/ai/analyze/comprehensive';
          break;
        case 'findings':
          endpoint = '/api/ai/extract/findings';
          break;
        case 'quality':
          endpoint = '/api/ai/assess/quality';
          break;
        default:
          return;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ arxiv_id: paper.arxiv_id })
      });

      const result = await response.json();
      setAnalysisResult({ type: analysisType, data: result });
      
      if (onAnalyze) {
        onAnalyze(paper.arxiv_id, result);
      }
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCitationAnalysis = async () => {
    if (onCitationAnalysis) {
      onCitationAnalysis(paper.arxiv_id);
    }
  };

  const openChat = () => {
    setIsChatOpen(true);
  };

  const handleGenerateShorts = async () => {
    setIsGeneratingShorts(true);
    
    const notification = document.createElement('div');
    notification.className = 'analysis-notification';
    notification.textContent = '🎬 쇼츠 생성 중... 잠시만 기다려주세요';
    document.body.appendChild(notification);
    
    try {
      const response = await fetch('http://localhost:5001/api/shorts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ arxiv_id: paper.arxiv_id })
      });
      
      if (response.ok) {
        const result = await response.json();
        notification.textContent = '✅ 쇼츠 생성 완료! 다운로드 준비됨';
        notification.style.backgroundColor = '#10b981';
        
        // 다운로드 링크 생성
        setTimeout(() => {
          const downloadLink = document.createElement('a');
          downloadLink.href = `http://localhost:5001/api/shorts/download/${paper.arxiv_id}`;
          downloadLink.download = `${paper.arxiv_id}_shorts.mp4`;
          downloadLink.click();
        }, 1000);
      } else {
        throw new Error('쇼츠 생성 실패');
      }
    } catch (error) {
      notification.textContent = '❌ 쇼츠 생성 실패: ' + error.message;
      notification.style.backgroundColor = '#ef4444';
    } finally {
      setIsGeneratingShorts(false);
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 3000);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getCategoryColors = (categories) => {
    const colorMap = {
      'cs.AI': '#3b82f6',
      'cs.LG': '#10b981',
      'cs.CL': '#f59e0b',
      'cs.CV': '#ef4444',
      'cs.CR': '#8b5cf6',
      'math': '#6366f1',
      'physics': '#06b6d4'
    };
    
    return categories.map(cat => 
      colorMap[cat] || colorMap[cat.split('.')[0]] || '#6b7280'
    );
  };

  const getPlatformInfo = (arxivId) => {
    if (!arxivId || typeof arxivId !== 'string') {
      return { platform: 'arxiv', icon: '📄', color: '#b45309' };
    }
    
    if (arxivId.includes(':')) {
      const platform = arxivId.split(':')[0];
      const platformMap = {
        'biorxiv': { platform: 'bioRxiv', icon: '🧬', color: '#059669' },
        'pmc': { platform: 'PMC', icon: '⚕️', color: '#dc2626' },
        'plos': { platform: 'PLOS', icon: '🔬', color: '#7c3aed' },
        'doaj': { platform: 'DOAJ', icon: '📚', color: '#0891b2' },
        'core': { platform: 'CORE', icon: '🌍', color: '#16a34a' }
      };
      return platformMap[platform] || { platform: platform.toUpperCase(), icon: '📋', color: '#6b7280' };
    }
    
    return { platform: 'arXiv', icon: '📄', color: '#b45309' };
  };

  const platformInfo = getPlatformInfo(paper.arxiv_id);

  return (
    <>
      <div className="enhanced-paper-card">
        <div className="paper-header">
          <div className="paper-metadata">
            <span 
              className="platform-badge" 
              style={{ backgroundColor: platformInfo.color }}
              title={`Source: ${platformInfo.platform}`}
            >
              {platformInfo.icon} {platformInfo.platform}
            </span>
            <span className="arxiv-id">{paper.arxiv_id}</span>
            <span className="publish-date">{formatDate(paper.published_date)}</span>
          </div>
          <div className="paper-actions">
            <button 
              className="action-btn chat-btn"
              onClick={openChat}
              title="AI 챗봇으로 논문 분석"
            >
              💬
            </button>
          </div>
        </div>

        <h3 className="paper-title" title={paper.title}>
          {paper.title}
        </h3>

        <div className="paper-authors">
          {paper.authors?.slice(0, 3).map((author, index) => (
            <span key={index} className="author-tag">
              {author}
            </span>
          ))}
          {paper.authors?.length > 3 && (
            <span className="author-more">+{paper.authors.length - 3} more</span>
          )}
        </div>

        <div className="paper-categories">
          {paper.categories?.slice(0, 4).map((category, index) => (
            <span 
              key={index} 
              className="category-tag"
              style={{ backgroundColor: getCategoryColors(paper.categories)[index] }}
            >
              {category}
            </span>
          ))}
        </div>

        <div className="paper-abstract">
          <p>
            {showFullAbstract 
              ? paper.abstract 
              : truncateText(paper.abstract, 300)
            }
          </p>
          {paper.abstract?.length > 300 && (
            <button 
              className="toggle-abstract"
              onClick={() => setShowFullAbstract(!showFullAbstract)}
            >
              {showFullAbstract ? '접기' : '더보기'}
            </button>
          )}
        </div>

        <div className="paper-actions-bar">
          <div className="primary-actions">
            <button 
              className="action-btn primary"
              onClick={() => handleQuickAnalysis('comprehensive')}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? '⏳' : '📊'} 종합분석
            </button>
            
            <button 
              className="action-btn secondary"
              onClick={() => handleQuickAnalysis('findings')}
              disabled={isAnalyzing}
            >
              🔍 핵심발견
            </button>
            
            <button 
              className="action-btn secondary"
              onClick={() => handleQuickAnalysis('quality')}
              disabled={isAnalyzing}
            >
              ⭐ 품질평가
            </button>
          </div>

          <div className="utility-actions">
            <button 
              className="action-btn utility"
              onClick={handleGenerateShorts}
              disabled={isGeneratingShorts}
              title="유튜브 쇼츠 생성"
            >
              {isGeneratingShorts ? '⏳' : '🎬'}
            </button>
            
            <button 
              className="action-btn utility"
              onClick={handleCitationAnalysis}
              title="인용 분석"
            >
              🔗
            </button>
            
            <a 
              href={paper.pdf_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="action-btn utility"
              title="PDF 보기"
            >
              📄
            </a>
          </div>
        </div>

        {analysisResult && (
          <AnalysisPreview 
            result={analysisResult} 
            onClose={() => setAnalysisResult(null)}
          />
        )}
      </div>

      <ChatBot 
        paperData={paper}
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        sessionId={`paper_${paper.arxiv_id}`}
      />
    </>
  );
};

const AnalysisPreview = ({ result, onClose }) => {
  const renderAnalysisContent = () => {
    const { type, data } = result;
    
    if (data.error) {
      return (
        <div className="analysis-error">
          <p>❌ 분석 중 오류가 발생했습니다: {data.error}</p>
        </div>
      );
    }

    switch (type) {
      case 'comprehensive':
        return (
          <div className="analysis-comprehensive">
            <h4>📊 종합 분석 결과</h4>
            {data.executive_summary && (
              <div className="analysis-section">
                <strong>요약:</strong>
                <p>{data.executive_summary}</p>
              </div>
            )}
            {data.quality_score && (
              <div className="analysis-section">
                <strong>품질 점수:</strong>
                <div className="score-display">
                  <span className="score-item">전체: {data.quality_score.overall}</span>
                  <span className="score-item">방법론: {data.quality_score.methodology_rigor}</span>
                  <span className="score-item">참신성: {data.quality_score.novelty}</span>
                </div>
              </div>
            )}
          </div>
        );

      case 'findings':
        return (
          <div className="analysis-findings">
            <h4>🔍 핵심 발견사항</h4>
            {data.main_findings && (
              <div className="analysis-section">
                <strong>주요 발견:</strong>
                <ul>
                  {data.main_findings.slice(0, 3).map((finding, idx) => (
                    <li key={idx}>{finding}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      case 'quality':
        return (
          <div className="analysis-quality">
            <h4>⭐ 품질 평가</h4>
            {data.quality_assessment && (
              <div className="quality-grid">
                <div className="quality-item">
                  <span>방법론</span>
                  <span>{data.quality_assessment.methodology_rigor}/100</span>
                </div>
                <div className="quality-item">
                  <span>참신성</span>
                  <span>{data.quality_assessment.novelty}/100</span>
                </div>
                <div className="quality-item">
                  <span>명확성</span>
                  <span>{data.quality_assessment.clarity}/100</span>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return <div>분석 결과를 표시할 수 없습니다.</div>;
    }
  };

  return (
    <div className="analysis-preview">
      <div className="analysis-header">
        <span>분석 결과</span>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      <div className="analysis-content">
        {renderAnalysisContent()}
      </div>
    </div>
  );
};

export default EnhancedPaperCard;
