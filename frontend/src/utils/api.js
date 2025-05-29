import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
});

export const paperAPI = {
  getPapers: (domain = 'all', daysBack = 7, limit = 50, category = null) =>
    apiClient.get('/papers', { params: { domain, days_back: daysBack, limit, category } }),
  
  getPaper: (id) =>
    apiClient.get(`/papers/${id}`),
  
  searchPapers: (query, category = null, maxResults = 10) =>
    apiClient.post('/search', { query, category, max_results: maxResults }),
    
  analyzePaper: (arxivId) => {
    console.log('DEBUG: api.js analyzePaper called with:', arxivId);
    console.log('DEBUG: Making POST request to /papers/analyze');
    console.log('DEBUG: Full URL will be:', apiClient.defaults.baseURL + '/papers/analyze');
    return apiClient.post('/papers/analyze', { arxiv_id: arxivId });
  },
    
  crawlPapers: (domain = 'all', daysBack = 7, limit = 10, category = null) =>
    apiClient.post('/crawl', { domain, days_back: daysBack, limit, category })
};

export default apiClient;
