import React, { useState, useEffect } from 'react';
import MultiPlatformSelector from './MultiPlatformSelector';
import './CrawlingSystem.css';

const CrawlingSystem = ({ activeSubTab = 'setup' }) => {
    const [crawlResults, setCrawlResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [platforms, setPlatforms] = useState({});
    const [statusMessage, setStatusMessage] = useState('Ready');
    const [papers, setPapers] = useState([]);

    useEffect(() => {
        loadPlatformStatus();
    }, []);

    useEffect(() => {
        if (activeSubTab === 'results') {
            loadRecentPapers();
        }
    }, [activeSubTab]);

    const loadPlatformStatus = async () => {
        try {
            const [platformsRes, statusRes] = await Promise.all([
                fetch('/api/v1/platforms'),
                fetch('/api/v1/crawling-status')
            ]);
            
            if (platformsRes.ok && statusRes.ok) {
                const platformsData = await platformsRes.json();
                const statusData = await statusRes.json();
                setPlatforms(platformsData.platforms || {});
                setStatusMessage(`Platform Status: ${statusData.active_platforms}/${statusData.total_platforms} active`);
            }
        } catch (error) {
            console.error('Platform status load error:', error);
            setStatusMessage('Platform status check failed');
        }
    };

    const handleCrawl = async (crawlRequest) => {
        setIsLoading(true);
        setStatusMessage('Multi-platform crawling in progress...');
        
        // 크롤링 시작 시간 저장
        const crawlStartTime = new Date().toISOString();
        
        try {
            const response = await fetch('/api/v1/multi-crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(crawlRequest)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                setCrawlResults(result);
                setStatusMessage(`크롤링 완료! 총 ${result.total_saved}개 논문 저장됨`);
                // 크롤링 시작 시간 이후 논문만 로드
                await loadPapersAfterTime(crawlStartTime);
                // 결과 탭으로 자동 전환
                switchToResultsTab();
            } else {
                setStatusMessage(`크롤링 실패: ${result.error}`);
            }
        } catch (error) {
            setStatusMessage(`Crawling error: ${error.message}`);
        }
        
        setIsLoading(false);
    };

    const handleArxivCrawl = async () => {
        setIsLoading(true);
        setStatusMessage('arXiv crawling in progress...');
        
        try {
            const response = await fetch('/api/v1/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: 'cs',
                    category: 'cs.AI',
                    days_back: 0,
                    limit: 20
                })
            });
            
            const result = await response.json();
            setStatusMessage(result.status === 'success' ? 
                `arXiv crawling completed: ${result.saved_count} papers saved` : 
                `arXiv crawling failed: ${result.error}`);
        } catch (error) {
            setStatusMessage(`arXiv crawling error: ${error.message}`);
        }
        
        setIsLoading(false);
    };

    const handleRSSCrawl = async () => {
        setIsLoading(true);
        setStatusMessage('RSS crawling in progress...');
        
        try {
            const response = await fetch('/api/v1/crawl-rss', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: 'cs',
                    category: 'cs.AI',
                    limit: 20
                })
            });
            
            const result = await response.json();
            setStatusMessage(result.status === 'success' ? 
                `RSS crawling completed: ${result.saved_count} papers saved` : 
                `RSS crawling failed: ${result.error}`);
        } catch (error) {
            setStatusMessage(`RSS crawling error: ${error.message}`);
        }
        
        setIsLoading(false);
    };

    const loadRecentPapers = async () => {
        try {
            const response = await fetch('/api/v1/papers?domain=all&days_back=0&limit=50');
            const papersData = await response.json();
            console.info('Recent papers loaded:', papersData.length);
            setPapers(Array.isArray(papersData) ? papersData : []);
            setStatusMessage(`${Array.isArray(papersData) ? papersData.length : 0} 방금 크롤링된 논문 로드됨`);
        } catch (error) {
            console.error('Paper load error:', error);
            setStatusMessage(`Paper load error: ${error.message}`);
        }
    };

    const loadPapersAfterTime = async (startTime) => {
        try {
            // 1초 대기 후 데이터베이스 동기화
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            console.log('=== 디버깅 시작 ===');
            console.log('크롤링 시작 시간:', startTime);
            
            const response = await fetch('/api/v1/papers?domain=all&days_back=0&limit=50');
            const papersData = await response.json();
            
            console.log('API에서 받은 총 논문 수:', papersData.length);
            console.log('첫 번째 논문:', papersData[0]);
            
            // 모든 논문을 일단 표시 (시간 필터링 제거)
            setPapers(Array.isArray(papersData) ? papersData : []);
            setStatusMessage(`총 ${papersData.length}개 논문 로드됨 (필터링 없음)`);
            
            console.log('=== 디버깅 완료 ===');
        } catch (error) {
            console.error('Paper load error:', error);
            setStatusMessage(`Paper load error: ${error.message}`);
        }
    };

    const switchToResultsTab = () => {
        if (window.switchToCrawlingResults) {
            window.switchToCrawlingResults();
        }
    };

    const renderSetupTab = () => (
        <div className="crawl-setup-tab">
            <h2>🚀 Multi-Platform Crawling Setup</h2>
            
            <div className="control-panel full-width">
                <MultiPlatformSelector 
                    onCrawl={handleCrawl}
                    isLoading={isLoading}
                    platformStatus={platforms}
                    onRefreshStatus={loadPlatformStatus}
                />
            </div>
        </div>
    );

    const renderResultsTab = () => (
        <div className="crawl-results-tab">
            <h2>📊 Crawling Results</h2>
            
            <div className="status-display" style={{margin: '20px 0', padding: '10px', background: '#f8f9fa', borderRadius: '4px'}}>
                {statusMessage}
            </div>
            
            <div className="papers-count" style={{margin: '10px 0', fontWeight: 'bold'}}>
                논문 수: {papers.length}개
            </div>
            
            <div className="paper-list">
                {papers.length === 0 ? (
                    <div style={{textAlign: 'center', padding: '40px', color: '#666'}}>
                        크롤링된 논문이 없습니다. 먼저 크롤링을 실행하세요.
                    </div>
                ) : (
                    papers.map((paper, index) => (
                        <div key={index} className="paper-item">
                            <div className="paper-actions">
                                <button className="small-btn primary">AI Analysis</button>
                                <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer" className="small-btn success">
                                    PDF
                                </a>
                            </div>
                            <div className="paper-title">{paper.title}</div>
                        <div className="paper-meta">
                            <strong>ID:</strong> {paper.paper_id} | 
                            <strong>Platform:</strong> {paper.platform || 'arxiv'} |
                            <strong>Authors:</strong> {Array.isArray(paper.authors) ? paper.authors.slice(0,2).join(', ') : paper.authors} | 
                            <strong>Published:</strong> {paper.published_date} |
                            <strong>Crawled:</strong> {paper.created_at}
                        </div>
                            <div className="paper-meta">
                                <strong>Categories:</strong> {Array.isArray(paper.categories) ? paper.categories.join(', ') : paper.categories}
                            </div>
                            <div className="paper-abstract">{paper.abstract?.substring(0, 300)}...</div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );

    return (
        <div className="crawling-system">
            <div className="tab-content">
                {activeSubTab === 'setup' && renderSetupTab()}
                {activeSubTab === 'results' && renderResultsTab()}
            </div>
        </div>
    );
};

export default CrawlingSystem;
