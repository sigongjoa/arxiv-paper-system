import React, { useState, useEffect } from 'react';
import MultiPlatformSelector from './MultiPlatformSelector';
import { systemAPI, paperAPI } from '../utils/api';
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
                systemAPI.getPlatforms(),
                systemAPI.getCrawlingStatus()
            ]);
            
            if (platformsRes.data && statusRes.data) {
                const platformsData = platformsRes.data;
                const statusData = statusRes.data;
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
        
        // 선택된 플랫폼 가져오기 (첫 번째 플랫폼 사용 또는 기본값 'all')
        const selectedPlatformForLoad = crawlRequest.platforms && crawlRequest.platforms.length > 0
            ? crawlRequest.platforms[0] : 'all';
        
        try {
            const response = await systemAPI.multiCrawl(crawlRequest);
            
            const result = response.data;
            
            if (result.status === 'success') {
                setCrawlResults(result);
                setStatusMessage(`크롤링 완료! 총 ${result.total_saved}개 논문 저장됨`);
                // 크롤링 시작 시간 이후 논문만 로드, 선택된 플랫폼 전달
                await loadPapersAfterTime(crawlStartTime, selectedPlatformForLoad);
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

    const loadRecentPapers = async (platform = 'all') => {
        try {
            console.log('CrawlingSystem: Loading recent papers...', { platform });
            // daysBack 값을 7로 고정 (또는 필요에 따라 변경)
            const daysBackValue = 7; 
            const response = await paperAPI.getPapers(platform, daysBackValue, 50);
            const papersData = response; // Fix: response is already the data array
            console.log('CrawlingSystem: Received papers data from API:', papersData);
            console.info('Recent papers loaded:', papersData.length);
            setPapers(Array.isArray(papersData) ? papersData : []);
            console.log('CrawlingSystem: Papers state updated with', Array.isArray(papersData) ? papersData.length : 0, 'papers.');
            setStatusMessage(`${Array.isArray(papersData) ? papersData.length : 0} 방금 크롤링된 논문 로드됨`);
        } catch (error) {
            console.error('Paper load error:', error);
            setStatusMessage(`Paper load error: ${error.message}`);
        }
    };

    const loadPapersAfterTime = async (crawlStartTime, platform = 'all') => {
        try {
            // 1초 대기 후 데이터베이스 동기화
            console.log('CrawlingSystem: Waiting 1 second for database sync before loading papers...');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            console.log('=== 디버깅 시작 ===');
            console.log('크롤링 시작 시간:', crawlStartTime);
            console.log('크롤링된 플랫폼:', platform);
            
            await loadRecentPapers(platform);
            
            console.log('CrawlingSystem: Finished loading papers after crawl.');
            console.log('=== 디버깅 완료 ===');
        } catch (error) {
            console.error('Paper load error in loadPapersAfterTime:', error);
            setStatusMessage(`Paper load error after crawl: ${error.message}`);
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
                {console.log('CrawlingSystem: Rendering results tab. Number of papers:', papers.length)}
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
                            <strong>Platform:</strong> {paper.platform} |
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
