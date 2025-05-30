import React, { useState, useEffect } from 'react';

const PaperList = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    period: 7,
    domain: 'cs',
    category: 'all',
    maxResults: 50,
    query: ''
  });

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/papers/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters)
      });
      if (!response.ok) throw new Error('검색 실패');
      const data = await response.json();
      setPapers(data);
      setError('');
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch('/api/papers/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ papers })
      });
      if (!response.ok) throw new Error('다운로드 실패');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'papers.json';
      a.click();
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    }
  };

  const handleSaveToDb = async () => {
    try {
      const response = await fetch('/api/papers/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ papers })
      });
      if (!response.ok) throw new Error('저장 실패');
      alert('데이터베이스에 저장되었습니다.');
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    }
  };

  return (
    <div>
      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">논문 검색</h2>
        </div>
        <div className="CardBody">
          {error && <div className="Error">{error}</div>}
          
          <div className="Grid">
            <div className="FormGroup">
              <label className="FormLabel">기간 (일)</label>
              <input
                type="number"
                className="FormControl"
                value={filters.period}
                onChange={(e) => setFilters({...filters, period: parseInt(e.target.value)})}
                min="1"
              />
            </div>
            <div className="FormGroup">
              <label className="FormLabel">도메인</label>
              <select
                className="FormControl"
                value={filters.domain}
                onChange={(e) => setFilters({...filters, domain: e.target.value})}
              >
                <option value="cs">Computer Science</option>
                <option value="math">Mathematics</option>
                <option value="physics">Physics</option>
                <option value="q-bio">Quantitative Biology</option>
                <option value="q-fin">Quantitative Finance</option>
              </select>
            </div>
            <div className="FormGroup">
              <label className="FormLabel">카테고리</label>
              <select
                className="FormControl"
                value={filters.category}
                onChange={(e) => setFilters({...filters, category: e.target.value})}
              >
                <option value="all">전체</option>
                <option value="cs.AI">AI</option>
                <option value="cs.CL">Computation and Language</option>
                <option value="cs.CV">Computer Vision</option>
                <option value="cs.LG">Machine Learning</option>
              </select>
            </div>
            <div className="FormGroup">
              <label className="FormLabel">최대 결과</label>
              <input
                type="number"
                className="FormControl"
                value={filters.maxResults}
                onChange={(e) => setFilters({...filters, maxResults: parseInt(e.target.value)})}
                min="1"
                max="100"
              />
            </div>
          </div>
          
          <div className="FormGroup">
            <input
              type="text"
              className="FormControl"
              placeholder="키워드, 저자, 제목으로 검색..."
              value={filters.query}
              onChange={(e) => setFilters({...filters, query: e.target.value})}
            />
          </div>
          
          <div style={{display: 'flex', gap: '1rem', justifyContent: 'space-between'}}>
            <button className="Button Button--primary" onClick={handleSearch} disabled={loading}>
              <i className="fas fa-search"></i> {loading ? '검색 중...' : '검색'}
            </button>
            <div style={{display: 'flex', gap: '1rem'}}>
              <button className="Button Button--primary" onClick={handleDownload} disabled={papers.length === 0}>
                <i className="fas fa-download"></i> 다운로드
              </button>
              <button className="Button Button--success" onClick={handleSaveToDb} disabled={papers.length === 0}>
                <i className="fas fa-database"></i> DB 저장
              </button>
            </div>
          </div>
        </div>
      </div>

      {loading && <div className="Loading">검색 중...</div>}
      
      {papers.length > 0 && (
        <div className="Grid">
          {papers.map((paper, index) => (
            <div key={index} className="Card">
              <div className="CardBody">
                <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>
                  {paper.title}
                </h3>
                <div style={{marginBottom: '0.75rem', fontSize: '0.875rem', color: 'var(--text-light)'}}>
                  <div><strong>저자:</strong> {paper.authors}</div>
                  <div><strong>카테고리:</strong> {paper.category}</div>
                  <div><strong>arXiv ID:</strong> {paper.arxiv_id}</div>
                  <div><strong>발행일:</strong> {paper.published}</div>
                </div>
                <p style={{marginBottom: '1rem', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical'}}>
                  {paper.abstract}
                </p>
                <div style={{display: 'flex', gap: '0.75rem'}}>
                  <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer" className="Button Button--primary">
                    <i className="fas fa-file-pdf"></i> PDF 보기
                  </a>
                  <button className="Button Button--success">
                    <i className="fas fa-robot"></i> AI 요약
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PaperList;
