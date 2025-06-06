import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 60000,
});

export const paperAPI = {
  getPapers: (domain = 'all', daysBack = 7, limit = 50, category = null) =>
    apiClient.get('/papers', { params: { domain, days_back: daysBack, limit, category } }),
  
  searchPapers: (query, category = null, maxResults = 10) =>
    apiClient.post('/search', { query, category, max_results: maxResults }),
    
  analyzePaper: (arxivId) =>
    apiClient.post('/papers/analyze', { arxiv_id: arxivId }),
    
  generateAnalysisPdf: (data) =>
    apiClient.post('/pdf/generate', data, { responseType: 'blob' }),
    
  crawlPapers: (domain = 'all', daysBack = 7, limit = 10, category = null) =>
    apiClient.post('/crawl', { domain, days_back: daysBack, limit, category }),

  crawlPapersRSS: (domain = 'cs', limit = 50, category = null) =>
    apiClient.post('/crawl-rss', { domain, limit, category }),

  getStats: () =>
    apiClient.get('/stats')
};

export const newsletterAPI = {
  create: (config) =>
    apiClient.post('/newsletter/create', config),
  
  test: (config) =>
    apiClient.post('/newsletter/test', config),
  
  getStatus: () =>
    apiClient.get('/newsletter/status')
};

export const mailingAPI = {
  getConfig: () =>
    apiClient.get('/mailing/config'),
  
  saveConfig: (config) =>
    apiClient.post('/mailing/config', config),
  
  testConfig: (config) =>
    apiClient.post('/mailing/test', config)
};

export const pdfAPI = {
  getList: () =>
    apiClient.get('/pdf/list'),
  
  view: (pdfId) =>
    apiClient.get(`/pdf/view/${pdfId}`, { responseType: 'blob' }),
  
  download: (pdfId) =>
    apiClient.get(`/pdf/download/${pdfId}`, { responseType: 'blob' }),
  
  delete: (pdfId) =>
    apiClient.delete(`/pdf/delete/${pdfId}`)
};

export default apiClient;
