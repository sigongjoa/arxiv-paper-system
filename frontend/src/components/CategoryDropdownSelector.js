import React, { useState, useEffect } from 'react';
import './CategoryDropdownSelector.css';

const CategoryDropdownSelector = ({ selectedPlatforms, onCategoryChange, onLimitChange, selectedCrawlingPlatform, onCrawlingPlatformChange }) => {
    const [platformCategories, setPlatformCategories] = useState({});
    const [loading, setLoading] = useState(false);
    const [selectedCategoryGroup, setSelectedCategoryGroup] = useState('');
    const [selectedCategories, setSelectedCategories] = useState([]);
    const [limit, setLimit] = useState(20);
    const [error, setError] = useState('');

    useEffect(() => {
        loadDetailedCategories();
    }, [selectedCrawlingPlatform]);

    const loadDetailedCategories = async () => {
        setLoading(true);
        setError('');

        if (!selectedCrawlingPlatform) {
            setPlatformCategories({});
            setLoading(false);
            return;
        }

        try {
            const response = await fetch(
                `/api/v1/platform-categories?platform=${encodeURIComponent(selectedCrawlingPlatform)}`
            );
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Status ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            
            console.log('Category API response:', data);
            
            if (data.success && data.categories) {
                setPlatformCategories(data.categories);
            } else {
                setError('카테고리 로드 실패');
                setPlatformCategories(getDefaultCategories());
            }
        } catch (error) {
            console.error('Category load error:', error);
            setError('API 연결 실패: ' + error.message);
            setPlatformCategories(getDefaultCategories());
        }
        setLoading(false);
    };

    const getDefaultCategories = () => {
        return {
            arxiv: {
                'All Categories': ['all'],
                'Computer Science': {
                    'cs.AI': 'Artificial Intelligence',
                    'cs.LG': 'Machine Learning',
                    'cs.CV': 'Computer Vision',
                    'cs.CL': 'Computation and Language',
                    'cs.NE': 'Neural and Evolutionary Computing',
                    'cs.RO': 'Robotics'
                },
                'Mathematics': {
                    'math.ST': 'Statistics Theory',
                    'math.PR': 'Probability',
                    'math.NA': 'Numerical Analysis'
                }
            },
            biorxiv: {
                'Life Sciences': ['Biochemistry', 'Bioinformatics', 'Cell Biology', 'Neuroscience'],
                'Medical Sciences': ['Epidemiology', 'Genetics', 'Immunology', 'Microbiology']
            },
            pmc: {
                'Medical Research': ['Medicine', 'Public Health', 'Clinical Research'],
                'Life Sciences': ['Biomedical Research', 'Genetics', 'Molecular Biology']
            },
            plos: {
                'Sciences': ['Biology', 'Computational Biology', 'Medicine']
            },
            doaj: {
                'Sciences': ['Computer Science', 'Engineering', 'Medicine'],
                'Social Sciences': ['Education', 'Psychology', 'Social Sciences']
            },
            core: {
                'All Subjects': ['Computer Science', 'Engineering', 'Medicine']
            }
        };
    };

    useEffect(() => {
        setSelectedCategoryGroup('');
        setSelectedCategories([]);
        onCategoryChange([]);
    }, [selectedCrawlingPlatform, onCategoryChange]);

    const handleCategoryGroupChange = (group) => {
        setSelectedCategoryGroup(group);
        
        if (group === 'All Categories') {
            setSelectedCategories(['all']);
            onCategoryChange(['all']);
        } else {
            const categoriesInGroup = getCategoriesFromGroup(selectedCrawlingPlatform, group);
            setSelectedCategories(categoriesInGroup);
            onCategoryChange(categoriesInGroup);
        }
    };

    const handleCategoryToggle = (category) => {
        const newCategories = selectedCategories.includes(category)
            ? selectedCategories.filter(c => c !== category)
            : [...selectedCategories, category];
        
        setSelectedCategories(newCategories);
        onCategoryChange(newCategories);
    };

    const handleSelectAllCategories = () => {
        if (!selectedCrawlingPlatform || !selectedCategoryGroup) return;
        
        const allCategories = getCategoriesFromGroup(selectedCrawlingPlatform, selectedCategoryGroup);
        const newCategories = selectedCategories.length === allCategories.length ? [] : allCategories;
        
        setSelectedCategories(newCategories);
        onCategoryChange(newCategories);
    };

    const handleLimitChange = (newLimit) => {
        setLimit(newLimit);
        onLimitChange(newLimit);
    };

    const availableCategoryGroups = selectedCrawlingPlatform 
        ? Object.keys(platformCategories[selectedCrawlingPlatform] || {}) 
        : [];
    
    const getCategoriesFromGroup = (platform, group) => {
        if (!platform || !group) return [];
        const categoryData = platformCategories[platform]?.[group];
        
        if (Array.isArray(categoryData)) {
            return categoryData;
        } else if (typeof categoryData === 'object') {
            return Object.keys(categoryData);
        }
        return [];
    };
    
    const availableCategories = getCategoriesFromGroup(selectedCrawlingPlatform, selectedCategoryGroup);

    const getCategoryDisplayName = (category) => {
        if (!selectedCrawlingPlatform || !selectedCategoryGroup) return category;
        
        const categoryData = platformCategories[selectedCrawlingPlatform]?.[selectedCategoryGroup];
        if (typeof categoryData === 'object' && !Array.isArray(categoryData)) {
            return categoryData[category] || category;
        }
        return category;
    };

    if (loading) {
        return (
            <div className="category-dropdown-selector loading">
                <h4>⏳ 카테고리 로딩 중...</h4>
                <div className="loading-message">세부 카테고리를 불러오고 있습니다.</div>
            </div>
        );
    }

    return (
        <div className="category-dropdown-selector">
            <h4>🔧 크롤링 설정</h4>
            
            {error && (
                <div className="error-message" style={{color: 'red', marginBottom: '10px'}}>
                    ⚠️ {error} (기본 카테고리 사용)
                </div>
            )}
            
            <div className="selector-row">
                <div className="selector-group">
                    <label>플랫폼:</label>
                    <select 
                        value={selectedCrawlingPlatform}
                        onChange={(e) => onCrawlingPlatformChange(e.target.value)}
                        className="platform-select"
                    >
                        <option value="">카테고리 선택할 플랫폼</option>
                        {selectedPlatforms.map(platform => (
                            <option key={platform} value={platform}>
                                {platform.toUpperCase()}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="selector-group">
                    <label>카테고리 그룹:</label>
                    <select 
                        value={selectedCategoryGroup} 
                        onChange={(e) => handleCategoryGroupChange(e.target.value)}
                        className="category-group-select"
                        disabled={!selectedCrawlingPlatform}
                    >
                        <option value="">세부 그룹 선택</option>
                        {availableCategoryGroups.map(group => (
                            <option key={group} value={group}>
                                {group}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="selector-group">
                    <label>최대 논문 수:</label>
                    <select 
                        value={limit} 
                        onChange={(e) => handleLimitChange(parseInt(e.target.value))}
                        className="limit-select"
                    >
                        <option value={10}>10개</option>
                        <option value={20}>20개</option>
                        <option value={50}>50개</option>
                        <option value={100}>100개</option>
                    </select>
                </div>
            </div>

            {availableCategories.length > 0 && (
                <div className="detailed-categories">
                    <div className="category-header">
                        <h5>📂 세부 카테고리 선택 ({availableCategories.length}개 사용가능):</h5>
                        <button 
                            className="select-all-btn"
                            onClick={handleSelectAllCategories}
                        >
                            {selectedCategories.length === availableCategories.length ? '🔄 전체 해제' : '☑️ 전체 선택'}
                        </button>
                    </div>
                    
                    <div className="category-grid">
                        {availableCategories.map(category => (
                            <label key={category} className="category-checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={selectedCategories.includes(category)}
                                    onChange={() => handleCategoryToggle(category)}
                                    className="category-checkbox"
                                />
                                <span className="category-code">{category}</span>
                                {getCategoryDisplayName(category) !== category && (
                                    <span className="category-description">
                                        {getCategoryDisplayName(category)}
                                    </span>
                                )}
                            </label>
                        ))}
                    </div>
                </div>
            )}

            {selectedCategories.length > 0 && (
                <div className="selected-summary">
                    <strong>✅ 선택된 카테고리 ({selectedCategories.length}개):</strong> 
                    <div className="selected-categories-list">
                        {selectedCategories.join(', ')}
                    </div>
                </div>
            )}

            {selectedCrawlingPlatform && availableCategories.length === 0 && (
                <div className="no-categories" style={{padding: '20px', textAlign: 'center', color: '#6c757d'}}>
                    ℹ️ {selectedCrawlingPlatform.toUpperCase()} 플랫폼의 세부 카테고리를 로드할 수 없습니다.
                </div>
            )}
        </div>
    );
};

export default CategoryDropdownSelector;