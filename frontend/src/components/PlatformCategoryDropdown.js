import React, { useState, useEffect } from 'react';

const PlatformCategoryDropdown = ({ selectedPlatforms, onCategoryChange, selectedCategories }) => {
    const [platformCategories] = useState({
        arxiv: ['Computer Science', 'Physics', 'Mathematics', 'Statistics', 'Electrical Engineering', 'Economics'],
        biorxiv: ['Bioinformatics', 'Biophysics', 'Cell Biology', 'Developmental Biology', 'Genetics', 'Immunology'],
        pmc: ['Medicine', 'Public Health', 'Clinical Research', 'Biomedical Research', 'Pharmacology'],
        plos: ['Biology', 'Medicine', 'Environmental Science', 'Genetics', 'Computational Biology'],
        doaj: ['Multidisciplinary', 'Social Sciences', 'Humanities', 'Engineering', 'Education'],
        core: ['Computer Science', 'Engineering', 'Medicine', 'Social Sciences', 'Natural Sciences']
    });

    const [platformSelections, setPlatformSelections] = useState({});

    useEffect(() => {
        const newSelections = {};
        selectedPlatforms.forEach(platform => {
            newSelections[platform] = selectedCategories.filter(cat => 
                platformCategories[platform]?.includes(cat)
            );
        });
        setPlatformSelections(newSelections);
    }, [selectedPlatforms, selectedCategories, platformCategories]);

    const handleCategorySelect = (platform, category) => {
        const currentSelections = { ...platformSelections };
        
        if (!currentSelections[platform]) {
            currentSelections[platform] = [];
        }

        if (currentSelections[platform].includes(category)) {
            currentSelections[platform] = currentSelections[platform].filter(c => c !== category);
        } else {
            currentSelections[platform] = [...currentSelections[platform], category];
        }

        setPlatformSelections(currentSelections);
        
        const allCategories = Object.values(currentSelections).flat();
        onCategoryChange(allCategories);
    };

    return (
        <div className="platform-category-dropdown">
            <h4>🏷️ 카테고리 선택 (플랫폼별)</h4>
            {selectedPlatforms.map(platform => (
                <div key={platform} className="platform-dropdown-section">
                    <div className="platform-dropdown-header">
                        <span className="platform-name">{platform.toUpperCase()}</span>
                        <span className="selected-count">
                            ({platformSelections[platform]?.length || 0}개 선택)
                        </span>
                    </div>
                    <div className="category-dropdown-grid">
                        {platformCategories[platform]?.map(category => (
                            <label key={category} className="category-checkbox-item">
                                <input
                                    type="checkbox"
                                    checked={platformSelections[platform]?.includes(category) || false}
                                    onChange={() => handleCategorySelect(platform, category)}
                                    className="category-checkbox"
                                />
                                <span className="category-label">{category}</span>
                            </label>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default PlatformCategoryDropdown;