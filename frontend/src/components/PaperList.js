import React, { useState, useEffect } from 'react';
import { paperAPI } from '../utils/api';
import PaperCard from './PaperCard';

const PaperList = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [category, setCategory] = useState('');
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    loadPapers();
  }, [page, category]);

  const loadPapers = async () => {
    setLoading(true);
    try {
      const response = await paperAPI.getPapers('all', 7, 50, category || null);
      setPapers(response.data || []);
      // Remove pagination for now since backend doesn't support it
      setTotalPages(1);
    } catch (error) {
      console.error('Error loading papers:', error);
      setPapers([]);
    }
    setLoading(false);
  };
  
  const handleCrawl = async () => {
    setCrawling(true);
    try {
      const response = await paperAPI.crawlPapers('all', 7, limit, category || null);
      console.log('Crawl result:', response.data);
      // Reload papers after crawling
      await loadPapers();
    } catch (error) {
      console.error('Crawling failed:', error);
    }
    setCrawling(false);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="PaperList">
      <div className="FilterSection">
        <select 
          value={category} 
          onChange={(e) => {
            setCategory(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All Categories</option>
          <option value="cs.AI">AI</option>
          <option value="cs.LG">Machine Learning</option>
          <option value="stat.ML">Statistics ML</option>
        </select>
        
        <input 
          type="number" 
          value={limit} 
          onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
          min="1" 
          max="100" 
          placeholder="Limit"
        />
        
        <button onClick={handleCrawl} disabled={crawling}>
          {crawling ? 'Crawling...' : 'Crawl Papers'}
        </button>
      </div>
      
      <div className="PapersGrid">
        {papers.map(paper => (
          <PaperCard key={paper.arxiv_id} paper={paper} />
        ))}
      </div>
      
      <div className="PaginationSection">
        <button 
          disabled={page <= 1} 
          onClick={() => setPage(page - 1)}
        >
          Previous
        </button>
        <span>Page {page} of {totalPages}</span>
        <button 
          disabled={page >= totalPages} 
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default PaperList;
