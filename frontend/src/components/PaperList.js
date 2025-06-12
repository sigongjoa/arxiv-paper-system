import React, { useState, useEffect, useRef } from 'react';
import { paperAPI, citationAPI, systemAPI, recommendationAPI } from '../utils/api';
import EnhancedPaperCard from './EnhancedPaperCard';
import MultiPlatformSelector from './MultiPlatformSelector';
import './PaperList.css';

const PaperList = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    domain: 'all',
    category: 'all',
    maxResults: 30,
    query: '',
    daysBack: 7
  });
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [viewMode, setViewMode] = useState('enhanced');
  const [analysisMode, setAnalysisMode] = useState(false);
  const [showMultiPlatform, setShowMultiPlatform] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    if (mountedRef.current) {
      loadInitialPapers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPlatforms]);

  useEffect(() => {
    mountedRef.current = true;
    loadInitialPapers();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (mountedRef.current) {
      // This effect can be simplified or removed if category dropdown is generalized
      // setFilters(prev => ({ ...prev, category: 'all' }));
    }
  }, [filters.domain]);

  const safeSetState = (setter, value) => {
    if (mountedRef.current) {
      setter(value);
    }
  };

  const showNotification = (message, type = 'success') => {
    try {
      const notification = document.createElement('div');
      notification.className = `analysis-notification ${type}`;
      notification.textContent = message;
      
      if (document.body) {
        document.body.appendChild(notification);
        
        setTimeout(() => {
          try {
            if (document.body && document.body.contains(notification)) {
              document.body.removeChild(notification);
            }
          } catch (e) {
            console.log('Notification cleanup error:', e);
          }
        }, 3000);
      }
    } catch (e) {
      console.log('Notification creation error:', e);
    }
  };

  const computeDomainParam = () => {
    // 플랫폼을 1개만 골랐을 때만 단일 검색, 그 외엔 'all' 또는 backend가
    // platforms 배열을 받을 수 있다면 빈 문자열 반환하고 querystring에 배열 추가
    if (selectedPlatforms.length === 1) return selectedPlatforms[0];
    return 'all';
  };

  const loadInitialPapers = async () => {
    safeSetState(setLoading, true);
    try {
      // Initial load uses default filters or general parameters
      const response = await paperAPI.getPapers(computeDomainParam(), filters.daysBack, filters.maxResults, filters.category === 'all' ? null : filters.category);
      const papersData = Array.isArray(response?.data) ? response.data : [];
      safeSetState(setPapers, papersData);
      safeSetState(setError, '');
    } catch (err) {
      console.error('Failed to load initial papers:', err);
      safeSetState(setPapers, []);
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const handleSearch = async () => {
    if (filters.query && filters.query.trim()) {
      await handleTextSearch();
    } else {
      await handleDomainSearch();
    }
  };

  const handleTextSearch = async () => {
    safeSetState(setLoading, true);
    try {
      const response = await recommendationAPI.searchPapersFaiss( // Changed to recommendationAPI.searchPapersFaiss
        filters.query, 
        filters.maxResults
      ); 
      const items = Array.isArray(response?.data?.results) ? response.data.results : []; // Changed to .results
      safeSetState(setPapers, items);
      safeSetState(setError, '');
    } catch (err) {
      const msg = err?.message || '검색 실패';
      safeSetState(setError, '검색 실패: ' + msg);
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const handleDomainSearch = async () => {
    safeSetState(setLoading, true);
    try {
      const response = await paperAPI.getPapers(
        computeDomainParam(), // Use computeDomainParam() here
        filters.daysBack,
        filters.maxResults,
        filters.category === 'all' ? null : filters.category
      );
      const papersData = Array.isArray(response?.data) ? response.data : [];
      safeSetState(setPapers, papersData);
      safeSetState(setError, '');
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || '논문 검색 실패';
      safeSetState(setError, '논문 검색 실패: ' + msg);
      safeSetState(setPapers, []);
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const handlePaperAnalysis = async (paperId, analysisResult) => { // Changed arxivId to paperId
    try {
      const paper = papers.find(p => p?.paper_id === paperId); // Changed arxivId to paper_id
      
      const pdfResponse = await paperAPI.generateAnalysisPdf({
        external_id: paperId, // Changed arxiv_id to external_id, using paperId
        title: paper?.title || 'Unknown Title',
        analysis: analysisResult // analysisResult is already stringified if it came from backend
      });
      
      if (window && typeof window.dispatchEvent === 'function') {
        window.dispatchEvent(new CustomEvent('loadPdf', {
          detail: {
            url: URL.createObjectURL(pdfResponse.data),
            name: `analysis_${paper?.platform || 'unknown'}_${paperId.replace('/', '_').replace('.', '_')}.pdf`, // Updated filename
            title: `AI Analysis: ${paper?.title || paperId}`
          }
        }));
      }
      
      showNotification('✅ AI 분석 완료! PDF 뷰어에서 확인하세요.');
      
    } catch (err) {
      console.error('Analysis handling failed:', err);
      showNotification('❌ 분석 처리 실패: ' + (err?.message || '알 수 없는 오류'), 'error');
    }
  };

  const handleCitationAnalysis = async (paperId) => { // Changed arxivId to paperId
    try {
      const extractResponse = await citationAPI.extractCitationData(paperId); // Changed arxivId to paperId
      
      if (!extractResponse.data?.success) {
        throw new Error('Citation extraction failed');
      }
      
      const analysisResponse = await citationAPI.analyzeCitationPatterns(paperId); // Changed arxivId to paperId
      const analysisData = analysisResponse.data;
      
      if (analysisData?.error) {
        throw new Error(analysisData.error);
      }
      
      const saveResponse = await citationAPI.saveCitationAnalysis(paperId, analysisData); // Changed arxivId to paperId
      const saveResult = saveResponse.data;
      
      if (saveResult?.success) {
        alert('🔗 인용 분석이 완료되어 Notion에 저장되었습니다!');
      } else {
        alert('⚠️ 인용 분석은 완료되었지만 Notion 저장에 실패했습니다.');
      }
      
    } catch (err) {
      console.error('인용 분석 처리 실패:', err);
      showNotification('❌ 인용 분석 처리 실패: ' + (err?.message || '알 수 없는 오류'), 'error');
    }
  };

  const handleDownload = () => {
    if (!Array.isArray(papers) || papers.length === 0) return;
    
    try {
      const dataStr = JSON.stringify(papers, null, 2);
      const dataBlob = new Blob([dataStr], {type: 'application/json'});
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `papers_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const handleSmartCrawl = async () => {
    safeSetState(setLoading, true);
    try {
      const requestBody = {
        query: filters.query || 'LLM', // 기본 쿼리 제공
        max_results: filters.maxResults,
        platforms: filters.domain === 'all' ? null : [filters.domain] // 'all'이면 모든 플랫폼, 아니면 선택된 플랫폼
      };
      showNotification('🚀 스마트 크롤링 시작...');
      const response = await systemAPI.smartCrawl(requestBody);
      if (response.data.status === 'success') {
        showNotification(`✅ 스마트 크롤링 완료: ${response.data.count}개의 새 논문 처리됨`);
        // 스마트 크롤링 후 최신 논문 다시 로드
        loadInitialPapers(); 
      } else {
        showNotification(`❌ 스마트 크롤링 실패: ${response.data.error}`, 'error');
      }
    } catch (err) {
      console.error('스마트 크롤링 에러:', err);
      showNotification('❌ 스마트 크롤링 실패: ' + (err?.message || '알 수 없는 오류'), 'error');
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const handleMultiPlatformCrawl = async (crawlRequest) => {
    safeSetState(setLoading, true);
    try {
      showNotification('🚀 다중 플랫폼 크롤링 시작...');
      const response = await systemAPI.multiCrawl({
        ...crawlRequest,
        platforms: crawlRequest.platforms // 필드명 보정
      });
      if (response.data.status === 'success') {
        showNotification(`✅ 다중 플랫폼 크롤링 완료: ${response.data.count}개의 새 논문 처리됨`);

        // Update filters to reflect the just-crawled parameters, then trigger search
        setFilters(prevFilters => ({
            ...prevFilters,
            domain: crawlRequest.platforms && crawlRequest.platforms.length > 0 ? crawlRequest.platforms[0] : 'all', // Assuming one platform for domain filter
            maxResults: crawlRequest.limit_per_platform || prevFilters.maxResults,
            daysBack: 0, // This is important to show newly crawled papers
            category: crawlRequest.categories && crawlRequest.categories.length > 0 ? crawlRequest.categories[0] : prevFilters.category
        }));
        handleDomainSearch(); // Reload papers based on updated filters
      } else {
        showNotification(`❌ 다중 플랫폼 크롤링 실패: ${response.data.error}`, 'error');
      }
    } catch (err) {
      console.error('다중 플랫폼 크롤링 에러:', err);
      showNotification('❌ 다중 플랫폼 크롤링 실패: ' + (err?.message || '알 수 없는 오류'), 'error');
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const safeArray = Array.isArray(papers) ? papers : [];

  return (
    <div className="paper-list-enhanced">
      <div className="paper-list-header">
        <div className="header-content">
          <h2>🔬 Paper Analysis Hub</h2>
          <p>AI-powered research paper discovery and analysis</p>
        </div>
        
        <div className="header-controls">
          <div className="view-mode-toggle">
            <button 
              className={`mode-btn ${viewMode === 'enhanced' ? 'active' : ''}`}
              onClick={() => setViewMode('enhanced')}
            >
              🤖 Enhanced
            </button>
            <button 
              className={`mode-btn ${viewMode === 'classic' ? 'active' : ''}`}
              onClick={() => setViewMode('classic')}
            >
              📄 Classic
            </button>
          </div>
        </div>
      </div>

      <div className="search-controls-enhanced">
        {error && <div className="alert-enhanced error">{error}</div>}
        
        <div className="controls-grid">
          <div className="control-group">
            <label className="control-label">Domain</label>
            <select
              className="form-control-enhanced"
              value={filters.domain}
              onChange={(e) => setFilters({...filters, domain: e.target.value})}
            >
              <option value="all">All Platforms</option>
              <option value="cs">Computer Science</option>
              <option value="math">Mathematics</option>
              <option value="physics">Physics</option>
            </select>
          </div>
          
          <div className="control-group">
            <label className="control-label">Category</label>
            <select
              className="form-control-enhanced"
              value={filters.category}
              onChange={(e) => setFilters({...filters, category: e.target.value})}
            >
              <option value="all">All Categories</option>
            </select>
          </div>
          
          <div className="control-group">
            <label className="control-label">Results</label>
            <input
              type="number"
              className="form-control-enhanced"
              value={filters.maxResults}
              onChange={(e) => setFilters({...filters, maxResults: parseInt(e.target.value) || 30})}
              min="5"
              max="100"
            />
          </div>
        </div>
        
        <div className="search-input-group">
          <input
            type="text"
            className="search-input-enhanced"
            placeholder="🔍 Search by keywords, authors, or titles..."
            value={filters.query}
            onChange={(e) => setFilters({...filters, query: e.target.value})}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="search-btn-enhanced" onClick={handleSearch} disabled={loading}>
            {loading ? '⏳' : '🔍'}
          </button>
        </div>
        
        <div className="action-bar">
          <div className="primary-actions">
            <button 
              className="btn-enhanced primary" 
              onClick={handleSearch} 
              disabled={loading}
            >
              <i className="fas fa-search"></i> 
              {loading ? 'Searching...' : 'Search Papers'}
            </button>
            
            <button 
              className="btn-enhanced success" 
              onClick={handleSmartCrawl} 
              disabled={loading}
            >
              <i className="fas fa-brain"></i> 
              Smart Crawl
            </button>
            
            <button 
              className="btn-enhanced" 
              onClick={() => setShowMultiPlatform(!showMultiPlatform)} 
              disabled={loading}
              style={{background: '#8b5cf6', color: 'white'}}
            >
              <i className="fas fa-globe"></i> 
              Multi-Platform
            </button>
          </div>
          
          <div className="utility-actions">
            <button 
              className="btn-enhanced secondary" 
              onClick={handleDownload} 
              disabled={safeArray.length === 0}
              title="Download as JSON"
            >
              <i className="fas fa-download"></i>
            </button>
            
            <button 
              className="btn-enhanced secondary"
              onClick={() => setAnalysisMode(!analysisMode)}
              title="Toggle Analysis Mode"
            >
              <i className={`fas ${analysisMode ? 'fa-eye-slash' : 'fa-eye'}`}></i>
            </button>
          </div>
        </div>
      </div>

      {showMultiPlatform && (
        <MultiPlatformSelector
          onCrawl={handleMultiPlatformCrawl}
          isLoading={loading}
          platformStatus={{}}
          onRefreshStatus={() => {}}
          onPlatformChange={setSelectedPlatforms}
        />
      )}

      {loading && (
        <div className="loading-enhanced">
          <div className="loading-spinner-enhanced"></div>
          <p>Processing your request...</p>
        </div>
      )}
      
      {!loading && safeArray.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-content">
            <h3>📚 No Papers Found</h3>
            <p>Start by crawling papers or try a different search query.</p>
            <button className="btn-enhanced success" onClick={handleSmartCrawl}>
              <i className="fas fa-brain"></i> Start Smart Crawl
            </button>
          </div>
        </div>
      )}
      
      {safeArray.length > 0 && (
        <div className="results-header">
          <div className="results-info">
            <h3>📊 Found {safeArray.length} papers</h3>
            <p>Displaying in {viewMode} mode</p>
          </div>
          
          <div className="results-actions">
            <button 
              className="btn-enhanced secondary"
              onClick={() => {
                const sorted = [...safeArray].sort((a, b) => {
                  const dateA = new Date(a?.published_date || 0);
                  const dateB = new Date(b?.published_date || 0);
                  return dateB - dateA;
                });
                setPapers(sorted);
              }}
            >
              📅 Sort by Date
            </button>
            
            <button 
              className="btn-enhanced secondary"
              onClick={() => {
                const sorted = [...safeArray].sort((a, b) => {
                  const titleA = a?.title || '';
                  const titleB = b?.title || '';
                  return titleA.localeCompare(titleB);
                });
                setPapers(sorted);
              }}
            >
              🔤 Sort by Title
            </button>
          </div>
        </div>
      )}
      
      {safeArray.length > 0 && (
        <div className={`papers-grid ${viewMode === 'enhanced' ? 'enhanced-grid' : 'classic-grid'}`}>
          {safeArray.map((paper, index) => {
            if (!paper) return null;
            
            return viewMode === 'enhanced' ? (
              <EnhancedPaperCard
                key={paper.paper_id || index}
                paper={paper}
                onAnalyze={handlePaperAnalysis}
                onCitationAnalysis={handleCitationAnalysis}
                showDetails={analysisMode}
              />
            ) : (
              <ClassicPaperCard
                key={paper.paper_id || index}
                paper={paper}
                onAnalyze={handlePaperAnalysis}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

const ClassicPaperCard = ({ paper, onAnalyze }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const response = await paperAPI.analyzePaper(paper?.paper_id);
      if (onAnalyze && paper?.paper_id) {
        onAnalyze(paper.paper_id, response?.data);
      }
    } catch (err) {
      console.error('Analysis failed:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!paper) return null;

  return (
    <div className="classic-paper-card">
      <div className="paper-content">
        <h3 className="paper-title">{paper.title || 'Untitled'}</h3>
        <div className="paper-meta">
          <div><strong>Authors:</strong> {Array.isArray(paper.authors) ? paper.authors.join(', ') : (paper.authors || 'Unknown')}</div>
          <div><strong>Categories:</strong> {Array.isArray(paper.categories) ? paper.categories.join(', ') : (paper.categories || 'Unknown')}</div>
          <div><strong>ID:</strong> {paper.paper_id} | <strong>Platform:</strong> {paper.platform || 'N/A'}</div>
          <div><strong>Published:</strong> {paper.published_date || 'Unknown'}</div>
        </div>
        <p className="paper-abstract">{paper.abstract || 'No abstract available'}</p>
      </div>
      <div className="paper-actions">
        {paper.pdf_url && (
          <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer" className="btn-enhanced primary">
            <i className="fas fa-file-pdf"></i> PDF
          </a>
        )}
        <button 
          className="btn-enhanced success" 
          onClick={handleAnalyze}
          disabled={isAnalyzing || !paper.paper_id}
        >
          <i className={isAnalyzing ? "fas fa-spinner fa-spin" : "fas fa-robot"}></i> 
          {isAnalyzing ? 'Analyzing...' : 'AI Summary'}
        </button>
      </div>
    </div>
  );
};

export default PaperList;