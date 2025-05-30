import React, { useState } from 'react';
import { paperAPI } from '../utils/api';

const PaperCard = ({ paper }) => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [parsedAnalysis, setParsedAnalysis] = useState(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  
  const handleAnalyze = async () => {
    console.log('DEBUG: Starting analysis for paper:', paper.arxiv_id);
    setAnalyzing(true);
    
    try {
      const response = await paperAPI.analyzePaper(paper.arxiv_id);
      console.log('DEBUG: Analysis response:', response.data);
      
      const analysisText = response.data.analysis;
      setAnalysis(analysisText);
      
      try {
        const parsed = JSON.parse(analysisText);
        setParsedAnalysis(parsed);
      } catch (e) {
        console.log('DEBUG: Failed to parse JSON, using raw text');
      }
      
      setShowAnalysis(true);
    } catch (error) {
      console.error('ERROR: Analysis failed:', error);
    }
    
    setAnalyzing(false);
  };
  return (
    <div className="PaperCard">
      <h3 className="PaperTitle">{paper.title}</h3>
      <div className="PaperMeta">
        <p><strong>저자:</strong> {Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors}</p>
        <p><strong>카테고리:</strong> {Array.isArray(paper.categories) ? paper.categories.join(', ') : paper.categories}</p>
        <p><strong>arXiv ID:</strong> {paper.arxiv_id}</p>
        <p><strong>발행일:</strong> {new Date(paper.published_date).toLocaleDateString()}</p>
      </div>
      <div className="PaperAbstract">
        {paper.abstract ? paper.abstract.substring(0, 300) + '...' : 'No abstract available'}
      </div>
      <div className="PaperActions">
        <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer" className="PdfLink">
          📄 PDF 보기
        </a>
        <button onClick={handleAnalyze} disabled={analyzing} className="AnalyzeButton">
          {analyzing ? '🤖 분석 중...' : '🧠 AI 분석하기'}
        </button>
        {showAnalysis && (
          <button onClick={() => setShowAnalysis(!showAnalysis)} className="ToggleButton">
            {showAnalysis ? '분석 숨기기' : '분석 보기'}
          </button>
        )}
      </div>
      
      {analyzing && (
        <div className="AnalyzingSection">
          <p>🤖 AI가 논문을 분석하고 있습니다...</p>
        </div>
      )}
      
      {showAnalysis && parsedAnalysis && (
        <div className="StructuredAnalysis">
          <h4>🤖 AI 분석 결과</h4>
          
          <div className="BackgroundSection">
            <h5>🎯 배경 및 문제 정의</h5>
            <p><strong>문제:</strong> {parsedAnalysis.background?.problem_definition || '분석 중...'}</p>
            <p><strong>동기:</strong> {parsedAnalysis.background?.motivation || '분석 중...'}</p>
          </div>
          
          <div className="ContributionsSection">
            <h5>💡 주요 기여</h5>
            <ul>
              {parsedAnalysis.contributions?.map((contrib, idx) => (
                <li key={idx}>{contrib}</li>
              )) || [
                <li key="default">주요 기여사항을 분석하고 있습니다...</li>
              ]}
            </ul>
          </div>
          
          <div className="MethodologySection">
            <h5>🔬 방법론</h5>
            <p><strong>접근법:</strong> {parsedAnalysis.methodology?.approach || '분석 중...'}</p>
            <p><strong>데이터셋:</strong> {parsedAnalysis.methodology?.datasets || '분석 중...'}</p>
          </div>
          
          {parsedAnalysis.results && (
            <div className="ResultsSection">
              <h5>📊 결과</h5>
              <p><strong>주요 발견:</strong> {parsedAnalysis.results.key_findings}</p>
              <p><strong>성능:</strong> {parsedAnalysis.results.performance}</p>
            </div>
          )}
        </div>
      )}
      
      {showAnalysis && analysis && !parsedAnalysis && (
        <div className="RawAnalysisSection">
          <h4>🤖 AI 분석 결과 (원문)</h4>
          <pre>{analysis}</pre>
        </div>
      )}
    </div>
  );
};

export default PaperCard;
