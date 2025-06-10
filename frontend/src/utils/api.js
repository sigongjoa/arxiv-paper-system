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
    apiClient.get('/stats'),
  
  multiCrawl: (domain, daysBack, category, limit) =>
    apiClient.post('/multi/crawl', { domain, days_back: daysBack, category, limit }),
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

export const aiAPI = {
  analyzeComprehensive: (arxivId) => apiClient.post('/ai/analyze/comprehensive', { arxiv_id: arxivId }),
  extractKeyFindings: (arxivId) => apiClient.post('/ai/extract/findings', { arxiv_id: arxivId }),
  assessPaperQuality: (arxivId) => apiClient.post('/ai/assess/quality', { arxiv_id: arxivId }),
  chatWithPaper: (sessionId, message, paperId = null) => apiClient.post('/ai/chat', { session_id: sessionId, message, paper_id: paperId }),
  clearChatHistory: (sessionId) => apiClient.delete(`/ai/chat/clear/${sessionId}`),
  generateResearchQuestions: (arxivId) => apiClient.post('/ai/generate/questions', { arxiv_id: arxivId }),
  getAIAgentStatus: () => apiClient.get('/ai/status'),
  getModelsStatus: () => apiClient.get('/enhanced/ai/enhanced/models/status'),
  optimizeSystem: () => apiClient.post('/enhanced/system/enhanced/optimize'),
  saveAnalysis: (arxivId, analysisData) => apiClient.post('/enhanced/save-analysis', { arxiv_id: arxivId, analysis_data: analysisData }),
  getResearchGaps: (arxivId) => apiClient.post('/enhanced/ai/enhanced/research-gaps', { arxiv_id: arxivId }),
  discoverResearch: (query) => apiClient.post('/agents/discover/research', { query }),
  getAgentsStatus: () => apiClient.get('/agents/status'),
  initializeAgents: (params) => apiClient.post('/agents/initialize', params),
  testAgentsConnection: () => apiClient.get('/agents/test/connection'),
  analyzePaperAgents: (arxivId) => apiClient.post('/agents/analyze/paper', { arxiv_id: arxivId }),
  analyzeCitationNetworkAgents: (arxivId) => apiClient.post('/agents/analyze/citation-network', { arxiv_id: arxivId }),
  suggestRelatedPapers: (arxivId) => apiClient.post('/ai/suggest/related', { arxiv_id: arxivId }),
  comparePapers: (arxivIds) => apiClient.post('/ai/compare', { arxiv_ids: arxivIds }),
};

export const recommendationAPI = {
  initializeSystem: () => apiClient.post('/recommendations/initialize'),
  getRecommendations: (params) => apiClient.post('/recommendations/get', params),
  getStatus: () => apiClient.get('/recommendations/status'),
  getSimilarPapers: (paperId, limit = 10) => apiClient.get(`/recommendations/similar/${paperId}`, { params: { limit } }),
  rebuildIndex: () => apiClient.post('/recommendations/rebuild'),
};

export const citationAPI = {
  extractCitationData: (arxivId) => apiClient.post(`/citation/extract/${arxivId}`),
  analyzeCitationPatterns: (arxivId) => apiClient.get(`/citation/analysis/${arxivId}`),
  getCitationNetwork: (arxivId, depth = 2) => apiClient.get(`/citation/network/${arxivId}`, { params: { depth } }),
  saveCitationAnalysis: (arxivId, data) => apiClient.post(`/citation/save-analysis/${arxivId}`, data), // This was in frontend, confirm backend
};

export const systemAPI = {
  getHealth: () => apiClient.get('/health'),
  getPlatforms: () => apiClient.get('/platforms'),
  getCrawlingStatus: () => apiClient.get('/crawling-status'),
  multiCrawl: (request) => apiClient.post('/multi-crawl', request),
  getMultiPlatforms: () => apiClient.get('/multi/platforms'),
  smartCrawl: (request) => apiClient.post('/enhanced/smart-crawl', request),
  getPDFStatus: () => apiClient.get('/pdf/status'),
  syncPDFs: () => apiClient.post('/pdf/sync'),
  getTest: () => apiClient.get('/test'),
};

export const categoryAPI = {
  getPlatformCategories: () => apiClient.get('/platform-categories'),
  getCategories: () => apiClient.get('/categories'),
};

export default apiClient;
