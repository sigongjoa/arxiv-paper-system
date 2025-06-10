import React, { useState, useEffect, useRef } from 'react';
import { paperAPI, citationAPI, systemAPI } from '../utils/api';
import { ARXIV_CATEGORIES } from '../utils/categories';
import EnhancedPaperCard from './EnhancedPaperCard';
import MultiPlatformSelector from './MultiPlatformSelector';
import './PaperList.css';

const PaperList = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    domain: 'cs',
    category: 'all',
    maxResults: 30,
    query: ''
  });
  const [viewMode, setViewMode] = useState('enhanced');
  const [analysisMode, setAnalysisMode] = useState(false);
  const [showMultiPlatform, setShowMultiPlatform] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    loadInitialPapers();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (mountedRef.current) {
      setFilters(prev => ({ ...prev, category: 'all' }));
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

  const loadInitialPapers = async () => {
    safeSetState(setLoading, true);
    try {
      const response = await paperAPI.getPapers('cs', 7, 30, null);
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
      const response = await paperAPI.searchPapers(
        filters.query, 
        filters.category === 'all' ? null : filters.category,
        filters.maxResults
      );
      const items = Array.isArray(response?.data?.items) ? response.data.items : [];
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
        filters.domain,
        0,
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

  const handleCrawl = async () => {
    safeSetState(setLoading, true);
    try {
      const response = await paperAPI.crawlPapers(
        filters.domain,
        0,
        filters.maxResults,
        filters.category === 'all' ? null : filters.category
      );
      
      console.log('API 크롤링 결과:', response);
      
      if (Array.isArray(response?.data) && response.data.length > 0) {
        safeSetState(setPapers, prev => {
          const existingIds = new Set((prev || []).map(p => p?.arxiv_id || p?.id).filter(Boolean));
          const newPapers = response.data.filter(p => p && !existingIds.has(p.arxiv_id || p.id));
          return [...newPapers, ...prev];
        });
      }
      
      showNotification('✅ API 크롤링 완료!');
      
    } catch (err) {
      console.error('API 크롤링 에러:', err);
      const errorMsg = err?.response?.data?.detail || err?.message || '크롤링 실패';
      safeSetState(setError, '크롤링 실패: ' + errorMsg);
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const handleRSSCrawl = async () => {
    safeSetState(setLoading, true);
    try {
      const response = await paperAPI.crawlPapersRSS(
        filters.domain,
        filters.maxResults,
        filters.category === 'all' ? null : filters.category
      );
      
      if (response?.data?.status === 'success') {
        console.log('RSS 크롤링 결과:', response.data);
        safeSetState(setError, '');
        
        if (Array.isArray(response.data.papers) && response.data.papers.length > 0) {
          safeSetState(setPapers, prev => {
            const existingIds = new Set((prev || []).map(p => p?.arxiv_id || p?.id).filter(Boolean));
            const newPapers = response.data.papers.filter(p => p && !existingIds.has(p.arxiv_id || p.id));
            return [...newPapers, ...prev];
          });
        }
        
        const count = response.data.saved_count || response.data.papers?.length || 0;
        showNotification(`✅ RSS 크롤링 완료! ${count}개 새 논문 저장됨`);
        
      } else {
        const errorMsg = response?.data?.error || 'RSS 크롤링 실패';
        safeSetState(setError, 'RSS 크롤링 실패: ' + errorMsg);
      }
    } catch (err) {
      console.error('RSS 크롤링 에러:', err);
      const errorMsg = err?.response?.data?.detail || err?.message || 'RSS 크롤링 실패';
      safeSetState(setError, 'RSS 크롤링 실패: ' + errorMsg);
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const handlePaperAnalysis = async (arxivId, analysisResult) => {
    try {
      const paper = papers.find(p => p?.arxiv_id === arxivId);
      
      const pdfResponse = await paperAPI.generateAnalysisPdf({
        arxiv_id: arxivId,
        title: paper?.title || 'Unknown Title',
        analysis: JSON.stringify(analysisResult)
      });
      
      if (window && typeof window.dispatchEvent === 'function') {
        window.dispatchEvent(new CustomEvent('loadPdf', {
          detail: {
            url: URL.createObjectURL(pdfResponse.data),
            name: `analysis_${arxivId}.pdf`,
            title: `AI Analysis: ${paper?.title || arxivId}`
          }
        }));
      }
      
      showNotification('✅ AI 분석 완료! PDF 뷰어에서 확인하세요.');
      
    } catch (err) {
      console.error('Analysis handling failed:', err);
      showNotification('❌ 분석 처리 실패: ' + (err?.message || '알 수 없는 오류'), 'error');
    }
  };

  const handleCitationAnalysis = async (arxivId) => {
    try {
      const extractResponse = await citationAPI.extractCitationData(arxivId);
      
      if (!extractResponse.data?.success) {
        throw new Error('Citation extraction failed');
      }
      
      const analysisResponse = await citationAPI.analyzeCitationPatterns(arxivId);
      const analysisData = analysisResponse.data;
      
      if (analysisData?.error) {
        throw new Error(analysisData.error);
      }
      
      const saveResponse = await citationAPI.saveCitationAnalysis(arxivId, analysisData);
      const saveResult = saveResponse.data;
      
      if (saveResult?.success) {
        alert('🔗 인용 분석이 완료되어 Notion에 저장되었습니다!');
      } else {
        alert('⚠️ 인용 분석은 완료되었지만 Notion 저장에 실패했습니다.');
      }
      
    } catch (err) {
      console.error('Citation analysis failed:', err);
      alert('❌ 인용 분석 실패: ' + (err?.message || '알 수 없는 오류'));
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
    if (!window.confirm('AI 기반 스마트 크롤링을 시작하시겠습니까? 시간이 더 오래 걸릴 수 있습니다.')) {
      return;
    }
    
    safeSetState(setLoading, true);
    try {
      const response = await systemAPI.smartCrawl({
        domain: filters.domain,
        category: filters.category === 'all' ? null : filters.category,
        days_back: 0,
        limit: filters.maxResults
      });
      
      if (response?.data?.status === 'success') {
        const newPapers = Array.isArray(response.data.papers) ? response.data.papers : [];
        if (newPapers.length > 0) {
          safeSetState(setPapers, prev => {
            const existingIds = new Set((prev || []).map(p => p?.arxiv_id || p?.id).filter(Boolean));
            return [...newPapers.filter(p => p && !existingIds.has(p.arxiv_id || p.id)), ...prev];
          });
        }
        showNotification('✅ Smart Crawl 완료!');
      } else {
        const errorMsg = response?.data?.error || 'Smart Crawl 실패';
        safeSetState(setError, 'Smart Crawl 실패: ' + errorMsg);
      }
    } catch (err) {
      console.error('Smart Crawl 에러:', err);
      const errorMsg = err?.response?.data?.detail || err?.message || 'Smart Crawl 실패';
      safeSetState(setError, 'Smart Crawl 실패: ' + errorMsg);
    } finally {
      safeSetState(setLoading, false);
    }
  };

  const handleMultiPlatformCrawl = async (crawlRequest) => {
    safeSetState(setLoading, true);
    try {
      const response = await paperAPI.multiCrawl(crawlRequest.domain, crawlRequest.days_back, crawlRequest.category, crawlRequest.limit);
      if (response?.data?.status === 'success') {
        const newPapers = Array.isArray(response.data.papers) ? response.data.papers : [];
        if (newPapers.length > 0) {
          safeSetState(setPapers, prev => {
            const existingIds = new Set((prev || []).map(p => p?.arxiv_id || p?.id).filter(Boolean));
            return [...newPapers.filter(p => p && !existingIds.has(p.arxiv_id || p.id)), ...prev];
          });
        }
        showNotification(`✅ 멀티플랫폼 크롤링 완료! ${response.data.saved_count || 0}개 논문 저장됨`);
      } else {
        const errorMsg = response?.data?.error || '멀티플랫폼 크롤링 실패';
        safeSetState(setError, '멀티플랫폼 크롤링 실패: ' + errorMsg);
      }
    } catch (err) {
      console.error('Multi-platform crawl error:', err);
      const errorMsg = err?.response?.data?.detail || err?.message || '멀티플랫폼 크롤링 실패';
      safeSetState(setError, '멀티플랫폼 크롤링 실패: ' + errorMsg);
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
              <option value="cs">🖥️ Computer Science</option>
              <option value="math">📐 Mathematics</option>
              <option value="physics">⚛️ Physics</option>
              <option value="all">🌐 All Domains</option>
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
              {filters.domain !== 'all' && ARXIV_CATEGORIES[filters.domain] && 
                Object.entries(ARXIV_CATEGORIES[filters.domain].categories).map(([key, value]) => (
                  <option key={key} value={key}>{key} - {value}</option>
                ))
              }
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
              onClick={handleCrawl} 
              disabled={loading}
            >
              <i className="fas fa-download"></i> 
              API Crawl
            </button>
            
            <button 
              className="btn-enhanced" 
              onClick={handleRSSCrawl} 
              disabled={loading}
              style={{background: '#17a2b8', color: 'white'}}
            >
              <i className="fas fa-rss"></i> 
              RSS Crawl
            </button>
            
            <button 
              className="btn-enhanced warning" 
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
            <button className="btn-enhanced success" onClick={handleCrawl}>
              <i className="fas fa-download"></i> Start Crawling
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
                key={paper.arxiv_id || index}
                paper={paper}
                onAnalyze={handlePaperAnalysis}
                onCitationAnalysis={handleCitationAnalysis}
                showDetails={analysisMode}
              />
            ) : (
              <ClassicPaperCard
                key={paper.arxiv_id || index}
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
      const response = await paperAPI.analyzePaper(paper?.arxiv_id);
      if (onAnalyze && paper?.arxiv_id) {
        onAnalyze(paper.arxiv_id, response?.data);
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
          <div><strong>arXiv ID:</strong> {paper.arxiv_id || 'Unknown'}</div>
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
          disabled={isAnalyzing || !paper.arxiv_id}
        >
          <i className={isAnalyzing ? "fas fa-spinner fa-spin" : "fas fa-robot"}></i> 
          {isAnalyzing ? 'Analyzing...' : 'AI Summary'}
        </button>
      </div>
    </div>
  );
};

export default PaperList;