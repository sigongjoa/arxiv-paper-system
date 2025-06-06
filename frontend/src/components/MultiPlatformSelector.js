import React, { useState, useEffect } from 'react';
import CategoryDropdownSelector from './CategoryDropdownSelector';
import './MultiPlatformSelector.css';

const MultiPlatformSelector = ({ onCrawl, isLoading, platformStatus = {}, onRefreshStatus }) => {
    // 플랫폼 기본 정보
    const defaultPlatforms = {
        arxiv: { available: true, status: 'active' },
        biorxiv: { available: true, status: 'active' },
        pmc: { available: true, status: 'active' },
        plos: { available: true, status: 'active' },
        doaj: { available: true, status: 'active' },
        core: { available: true, status: 'needs_api_key' }
    };

    const [platforms, setPlatforms] = useState(defaultPlatforms);
    const [selectedPlatforms, setSelectedPlatforms] = useState(['arxiv']);
    const [selectedCategories, setSelectedCategories] = useState([]);
    const [crawlLimit, setCrawlLimit] = useState(20);



    useEffect(() => {
        checkPlatformStatus();
    }, [selectedPlatforms]);

    useEffect(() => {
        // platformStatus가 변경되면 플랫폼 상태 업데이트
        if (Object.keys(platformStatus).length > 0) {
            const updatedPlatforms = { ...defaultPlatforms };
            Object.keys(platformStatus).forEach(platform => {
                if (updatedPlatforms[platform]) {
                    updatedPlatforms[platform].status = platformStatus[platform].status;
                    updatedPlatforms[platform].message = platformStatus[platform].message;
                }
            });
            setPlatforms(updatedPlatforms);
        }
    }, [platformStatus]);

    const checkPlatformStatus = async () => {
        // 백그라운드에서 플랫폼 상태 확인 (선택적)
        try {
            const response = await fetch('/api/v1/multi/platforms');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // API 응답이 있으면 상태 업데이트
                    const updatedPlatforms = { ...defaultPlatforms };
                    Object.keys(data.platforms).forEach(platform => {
                        if (updatedPlatforms[platform]) {
                            updatedPlatforms[platform].available = data.platforms[platform];
                        }
                    });
                    setPlatforms(updatedPlatforms);
                }
            }
        } catch (error) {
            console.log('플랫폼 상태 확인 실패 (기본값 사용):', error);
        }
    };

    const handlePlatformToggle = (platform) => {
        const platformData = platforms[platform];
        if (!platformData || !platformData.available) return;
        
        setSelectedPlatforms(prev => {
            const newSelected = prev.includes(platform) 
                ? prev.filter(p => p !== platform)
                : [...prev, platform];
            return newSelected;
        });
    };

    const handleSelectAll = () => {
        const availablePlatforms = Object.keys(platforms).filter(platform => 
            platforms[platform] && platforms[platform].available
        );
        if (selectedPlatforms.length === availablePlatforms.length) {
            setSelectedPlatforms([]);
        } else {
            setSelectedPlatforms(availablePlatforms);
        }
    };

    const handleCategoryChange = (categories) => {
        setSelectedCategories(categories);
    };

    const handleLimitChange = (limit) => {
        setCrawlLimit(limit);
    };

    const handleApiCrawl = () => {
        if (selectedPlatforms.length === 0) {
            alert('최소 하나의 플랫폼을 선택해주세요.');
            return;
        }

        const crawlRequest = {
            platforms: selectedPlatforms,
            categories: selectedCategories,
            days_back: 7,
            limit_per_platform: crawlLimit,
            crawl_type: 'api'
        };

        onCrawl(crawlRequest);
    };

    const handleRssCrawl = () => {
        if (selectedPlatforms.length === 0) {
            alert('최소 하나의 플랫폼을 선택해주세요.');
            return;
        }

        const crawlRequest = {
            platforms: selectedPlatforms,
            categories: selectedCategories,
            days_back: 7,
            limit_per_platform: crawlLimit,
            crawl_type: 'rss'
        };

        onCrawl(crawlRequest);
    };

    const getPlatformStatus = (platform) => {
        const platformData = platforms[platform];
        if (!platformData) return 'unavailable';
        
        if (!platformData.available) {
            return 'needs-config';
        }
        
        // 실제 백엔드 상태 확인
        if (platformStatus[platform]) {
            return platformStatus[platform].status === 'success' ? 'available' : 'error';
        }
        
        return 'available';
    };

    const getPlatformStatusMessage = (platform) => {
        if (platformStatus[platform]) {
            return platformStatus[platform].message || '';
        }
        return '';
    };

    const getPlatformIcon = (platform) => {
        const icons = {
            arxiv: '📄',
            biorxiv: '🧬',
            pmc: '⚕️',
            plos: '🔬',
            doaj: '📚',
            core: '🌍'
        };
        return icons[platform] || '📋';
    };

    const getPlatformInfo = (platform) => {
        const platformDetails = {
            arxiv: {
                fullName: 'arXiv.org',
                description: '물리학, 수학, 컴퓨터과학 프리프린트 서버',
                features: ['무료', '빠른 업데이트', '고품질']
            },
            biorxiv: {
                fullName: 'bioRxiv / medRxiv',
                description: '생명과학 및 의학 연구 프리프린트',
                features: ['무료', '제한없음', '생명과학']
            },
            pmc: {
                fullName: 'PubMed Central',
                description: 'NIH 공공 의학 논문 데이터베이스',
                features: ['의학', '전문텍스트', '고신뢰성']
            },
            plos: {
                fullName: 'PLOS (Public Library of Science)',
                description: '공공 과학 도서관 - 오픈 액세스 논문',
                features: ['오픈액세스', '다양한 분야', '고품질']
            },
            doaj: {
                fullName: 'Directory of Open Access Journals',
                description: '오픈 액세스 저널 디렉토리',
                features: ['오픈액세스', '저널중심', '다국어']
            },
            core: {
                fullName: 'CORE (COnnecting REpositories)',
                description: '세계 최대 학술 논문 집합체 (2억개+)',
                features: ['대용량', 'API키필수', '전세계']
            }
        };
        return platformDetails[platform] || {
            fullName: platform.toUpperCase(),
            description: '알 수 없는 플랫폼',
            features: ['알 수 없음']
        };
    };

    return (
        <div className="multi-platform-selector">
            {/* 플랫폼 선택 */}
            <div className="platform-selection">
                <div className="platform-header">
                    <h4>📊 플랫폼 선택 및 상태</h4>
                    {onRefreshStatus && (
                        <button 
                            className="refresh-status-btn"
                            onClick={onRefreshStatus}
                            title="플랫폼 상태 새로고침"
                        >
                            🔄 상태 새로고침
                        </button>
                    )}
                </div>
                <div className="platform-table-container">
                    <table className="platform-table">
                        <thead>
                            <tr>
                                <th>
                                    <input
                                        type="checkbox"
                                        checked={selectedPlatforms.length > 0 && selectedPlatforms.length === Object.keys(platforms).filter(p => platforms[p] && platforms[p].available).length}
                                        onChange={handleSelectAll}
                                        className="platform-checkbox"
                                        title="전체 선택/해제"
                                    />
                                </th>
                                <th>플랫폼</th>
                                <th>설명</th>
                                <th>상태</th>
                                <th>특징</th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.keys(platforms).map(platform => {
                                const platformInfo = getPlatformInfo(platform);
                                const status = getPlatformStatus(platform);
                                return (
                                    <tr 
                                        key={platform}
                                        className={`platform-row ${selectedPlatforms.includes(platform) ? 'selected' : ''} ${status}`}
                                        onClick={() => {
                                            const platformData = platforms[platform];
                                            if (platformData && platformData.available) {
                                                handlePlatformToggle(platform);
                                            }
                                        }}
                                    >
                                        <td className="checkbox-cell">
                                            <input
                                                type="checkbox"
                                                checked={selectedPlatforms.includes(platform)}
                                                onChange={(e) => {
                                                    e.stopPropagation();
                                                    const platformData = platforms[platform];
                                                    if (platformData && platformData.available) {
                                                        handlePlatformToggle(platform);
                                                    }
                                                }}
                                                disabled={!platforms[platform] || !platforms[platform].available}
                                                className="platform-checkbox"
                                            />
                                        </td>
                                        <td className="platform-cell">
                                            <div className="platform-info">
                                                <span className="platform-icon">{getPlatformIcon(platform)}</span>
                                                <div className="platform-details">
                                                    <div className="platform-name">{platform.toUpperCase()}</div>
                                                    <div className="platform-full-name">{platformInfo.fullName}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="description-cell">
                                            <span className="platform-description">{platformInfo.description}</span>
                                        </td>
                                        <td className="status-cell">
                                            <div className="status-info">
                                                <span className={`status-badge ${status}`}>
                                                    {status === 'available' ? '✅ 사용 가능' : 
                                                     status === 'needs-config' ? '⚙️ 설정 필요' : 
                                                     status === 'error' ? '❌ 오류' : '❌ 사용 불가'}
                                                </span>
                                                {getPlatformStatusMessage(platform) && (
                                                    <div className="status-message">
                                                        {getPlatformStatusMessage(platform)}
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="features-cell">
                                            <div className="platform-features">
                                                {platformInfo.features.map((feature, idx) => (
                                                    <span key={idx} className="feature-tag">{feature}</span>
                                                ))}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
                <div className="selection-summary">
                    선택된 플랫폼: {selectedPlatforms.length}개 
                    {selectedPlatforms.length > 0 && (
                        <span className="selected-list">
                            ({selectedPlatforms.map(p => p.toUpperCase()).join(', ')})
                        </span>
                    )}
                </div>
            </div>

            {/* 카테고리 선택 */}
            <CategoryDropdownSelector 
                selectedPlatforms={selectedPlatforms}
                onCategoryChange={handleCategoryChange}
                onLimitChange={handleLimitChange}
            />

            {/* 크롤링 버튼 */}
            <div className="crawl-actions">
                <div className="crawl-buttons">
                    <button 
                        className="crawl-button api"
                        onClick={handleApiCrawl}
                        disabled={isLoading || selectedPlatforms.length === 0}
                    >
                        {isLoading ? (
                            <span>
                                <span className="spinner"></span>
                                API 크롤링 중...
                            </span>
                        ) : (
                            <span>
                                🚀 API 크롤링 시작
                            </span>
                        )}
                    </button>
                    
                    <button 
                        className="crawl-button rss"
                        onClick={handleRssCrawl}
                        disabled={isLoading || selectedPlatforms.length === 0}
                    >
                        {isLoading ? (
                            <span>
                                <span className="spinner"></span>
                                RSS 크롤링 중...
                            </span>
                        ) : (
                            <span>
                                📡 RSS 크롤링 시작
                            </span>
                        )}
                    </button>
                </div>
                
                <div className="crawl-info">
                    선택된 플랫폼: {selectedPlatforms.length}개
                </div>
            </div>
        </div>
    );
};

export default MultiPlatformSelector;