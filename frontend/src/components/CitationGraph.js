import React, { useState, useEffect, useRef } from 'react';
import './CitationGraph.css';

const CitationGraph = () => {
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [manualInput, setManualInput] = useState('');
  const [status, setStatus] = useState('논문을 선택하고 Citation Graph를 생성하세요');
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [graphDepth, setGraphDepth] = useState(2);
  const [maxNodes, setMaxNodes] = useState(100);
  const [cytoscapeInstance, setCytoscapeInstance] = useState(null);
  const graphContainerRef = useRef(null);

  // 논문 목록 로드
  useEffect(() => {
    loadPapers();
  }, []);

  // Cytoscape.js 로드
  useEffect(() => {
    if (!window.cytoscape) {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js';
      script.onload = () => {
        const layoutScript = document.createElement('script');
        layoutScript.src = 'https://unpkg.com/cytoscape-cose-bilkent@4.1.0/cytoscape-cose-bilkent.js';
        document.head.appendChild(layoutScript);
      };
      document.head.appendChild(script);
    }
  }, []);

  const loadPapers = async () => {
    try {
      const response = await fetch('/api/v1/papers?domain=all&days_back=30&limit=100');
      const data = await response.json();
      setPapers(data);
    } catch (error) {
      console.error('논문 로드 실패:', error);
    }
  };

  const selectPaper = (paper) => {
    setSelectedPaper({
      id: paper.arxiv_id,
      title: paper.title
    });
    setStatus(`선택된 논문: ${paper.title.substring(0, 50)}...`);
  };

  const selectManualPaper = () => {
    const arxivId = manualInput.trim();
    if (!arxivId) {
      alert('arXiv ID를 입력하세요 (예: 2101.00001)');
      return;
    }
    
    setSelectedPaper({ id: arxivId, title: `arXiv:${arxivId}` });
    setManualInput('');
    setStatus(`선택된 논문: ${arxivId}`);
  };

  const loadCitationGraph = async () => {
    if (!selectedPaper) {
      setStatus('논문을 먼저 선택하세요');
      return;
    }

    setLoading(true);
    setStatus('📊 Citation 데이터 추출 중...');

    try {
      // 1. Citation 데이터 추출
      const extractResponse = await fetch(`/api/v1/citation/extract/${selectedPaper.id}`, {
        method: 'POST'
      });
      const extractResult = await extractResponse.json();
      
      if (!extractResult.success) {
        setStatus(`❌ Citation 추출 실패: ${extractResult.error}`);
        setLoading(false);
        return;
      }

      setStatus('🔍 Citation 네트워크 생성 중...');
      
      // 2. 네트워크 데이터 조회
      const networkResponse = await fetch(`/api/v1/citation/network/${selectedPaper.id}?depth=${graphDepth}`);
      const networkData = await networkResponse.json();
      
      if (!networkData.nodes || networkData.nodes.length === 0) {
        setStatus('⚠️ Citation 데이터가 없습니다');
        setLoading(false);
        return;
      }

      // 3. 노드 수 제한
      if (networkData.nodes.length > maxNodes) {
        networkData.nodes = networkData.nodes.slice(0, maxNodes);
        const nodeIds = networkData.nodes.map(n => n.data.id);
        networkData.edges = networkData.edges.filter(e => 
          nodeIds.includes(e.data.source) && nodeIds.includes(e.data.target)
        );
      }

      setStatus('🎨 그래프 렌더링 중...');
      renderCitationGraph(networkData);
      setStatus(`✅ Citation Graph 생성 완료! (노드: ${networkData.nodes.length}, 엣지: ${networkData.edges.length})`);

    } catch (error) {
      setStatus(`❌ 오류: ${error.message}`);
    }
    
    setLoading(false);
  };

  const renderCitationGraph = (networkData) => {
    if (!window.cytoscape || !graphContainerRef.current) {
      setStatus('❌ Cytoscape 라이브러리 로딩 중...');
      return;
    }

    if (cytoscapeInstance) {
      cytoscapeInstance.destroy();
    }

    const cy = window.cytoscape({
      container: graphContainerRef.current,
      elements: [...networkData.nodes, ...networkData.edges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': function(ele) {
              return ele.data('type') === 'center' ? '#e74c3c' : '#3498db';
            },
            'width': function(ele) {
              return Math.max(30, Math.log(ele.data('citation_count') + 1) * 15);
            },
            'height': function(ele) {
              return Math.max(30, Math.log(ele.data('citation_count') + 1) * 15);
            },
            'label': 'data(label)',
            'font-size': '12px',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '120px',
            'color': '#2c3e50',
            'text-outline-width': 2,
            'text-outline-color': 'white',
            'border-width': 2,
            'border-color': '#34495e'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#bdc3c7',
            'target-arrow-color': '#bdc3c7',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'node:selected',
          style: {
            'background-color': '#f39c12',
            'border-width': 4,
            'border-color': '#e67e22'
          }
        }
      ],
      layout: {
        name: 'cose-bilkent',
        animate: true,
        animationDuration: 1000,
        fit: true,
        padding: 50
      }
    });

    // 노드 클릭 이벤트
    cy.on('tap', 'node', function(evt) {
      const nodeData = evt.target.data();
      setStatus(`선택된 노드: ${nodeData.label} (인용수: ${nodeData.citation_count || 0})`);
    });

    setCytoscapeInstance(cy);
  };

  const analyzeCitationPatterns = async () => {
    if (!selectedPaper) {
      setStatus('논문을 먼저 선택하세요');
      return;
    }
    
    setLoading(true);
    setStatus('📈 인용 패턴 분석 중...');
    
    try {
      const response = await fetch(`/api/v1/citation/analysis/${selectedPaper.id}`);
      const result = await response.json();
      
      if (result.error) {
        setStatus(`❌ 분석 실패: ${result.error}`);
      } else {
        const analysis = result.analysis || {};
        setStatus(`✅ 분석 완료 - 인용수: ${analysis.citation_count || 0}, 참고문헌: ${analysis.reference_count || 0}, 영향력: ${(analysis.impact_score || 0).toFixed(2)}`);
      }
    } catch (error) {
      setStatus(`❌ 분석 오류: ${error.message}`);
    }
    
    setLoading(false);
  };

  // 논문 필터링
  const filteredPapers = papers.filter(paper => 
    paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    paper.arxiv_id.includes(searchQuery) ||
    paper.authors.some(author => author.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="citation-main-container">
      <h2>📊 Citation Tracking System</h2>
      
      <div className="citation-layout">
        {/* 왼쪽: 논문 선택 */}
        <div className="paper-selection-panel">
          <h3>📋 논문 선택</h3>
          
          {/* 수동 입력 */}
          <div className="manual-input-section">
            <h4>직접 입력</h4>
            <div className="input-group">
              <input
                type="text"
                value={manualInput}
                onChange={(e) => setManualInput(e.target.value)}
                placeholder="arXiv ID (예: 2101.00001)"
                className="arxiv-input"
              />
              <button onClick={selectManualPaper} className="btn btn-primary">
                선택
              </button>
            </div>
          </div>

          {/* 검색 */}
          <div className="search-section">
            <h4>DB에서 검색</h4>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="제목, 저자, arXiv ID로 검색..."
              className="search-input"
            />
          </div>

          {/* 논문 목록 테이블 */}
          <div className="papers-table-container">
            <table className="papers-table">
              <thead>
                <tr>
                  <th>arXiv ID</th>
                  <th>제목</th>
                  <th>저자</th>
                  <th>선택</th>
                </tr>
              </thead>
              <tbody>
                {filteredPapers.slice(0, 20).map((paper, index) => (
                  <tr key={index} className={selectedPaper?.id === paper.arxiv_id ? 'selected' : ''}>
                    <td className="arxiv-id">{paper.arxiv_id}</td>
                    <td className="title">{paper.title.substring(0, 60)}...</td>
                    <td className="authors">{paper.authors.slice(0, 2).join(', ')}{paper.authors.length > 2 ? '...' : ''}</td>
                    <td>
                      <button 
                        onClick={() => selectPaper(paper)}
                        className="btn btn-sm btn-select"
                      >
                        선택
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredPapers.length === 0 && (
              <div className="no-results">검색 결과가 없습니다</div>
            )}
          </div>
        </div>

        {/* 오른쪽: Citation Graph */}
        <div className="citation-graph-panel">
          {/* 선택된 논문 정보 */}
          <div className="selected-paper-info">
            <strong>선택된 논문:</strong> {selectedPaper ? selectedPaper.title : '논문을 선택하세요'}
          </div>

          {/* 설정 */}
          <div className="graph-settings">
            <div className="setting-item">
              <label>깊이:</label>
              <input
                type="number"
                value={graphDepth}
                onChange={(e) => setGraphDepth(parseInt(e.target.value))}
                min="1"
                max="3"
                className="small-input"
              />
              <span>단계</span>
            </div>
            <div className="setting-item">
              <label>최대 노드:</label>
              <input
                type="number"
                value={maxNodes}
                onChange={(e) => setMaxNodes(parseInt(e.target.value))}
                min="20"
                max="500"
                className="small-input"
              />
              <span>개</span>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="action-buttons">
            <button 
              onClick={loadCitationGraph} 
              className="btn btn-primary"
              disabled={loading || !selectedPaper}
            >
              📊 Citation Graph 생성
            </button>
            <button 
              onClick={analyzeCitationPatterns} 
              className="btn btn-secondary"
              disabled={loading || !selectedPaper}
            >
              📈 인용 분석
            </button>
          </div>

          {/* 상태 표시 */}
          <div className={`status-display ${loading ? 'loading' : ''}`}>
            {status}
          </div>

          {/* 그래프 컨테이너 */}
          <div className="graph-container">
            <div ref={graphContainerRef} className="cytoscape-container"></div>
            
            {!cytoscapeInstance && (
              <div className="graph-placeholder">
                Citation Graph가 여기에 표시됩니다
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CitationGraph;
