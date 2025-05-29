import React, { useState, useEffect } from 'react';
import { paperAPI } from '../utils/api';

const PaperCard = ({ paper }) => {
  console.log('DEBUG: PaperCard component rendered for paper:', paper?.arxiv_id);
  
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [parsedAnalysis, setParsedAnalysis] = useState(null);
  
  useEffect(() => {
    console.log('DEBUG: PaperCard useEffect triggered for paper:', paper.arxiv_id);
    handleAnalyze();
  }, [paper.arxiv_id]);
  
  const handleAnalyze = async () => {
    console.log('DEBUG: Starting analysis for paper:', paper.arxiv_id);
    console.log('DEBUG: Paper title:', paper.title);
    console.log('DEBUG: API endpoint will be called');
    setAnalyzing(true);
    
    const response = await paperAPI.analyzePaper(paper.arxiv_id);
    console.log('DEBUG: Analysis response status:', response.status);
    console.log('DEBUG: Analysis response data:', response.data);
    
    const analysisText = response.data.analysis;
    console.log('DEBUG: Analysis text length:', analysisText.length);
    console.log('DEBUG: Analysis text preview:', analysisText.substring(0, 100));
    setAnalysis(analysisText);
    
    // Try to parse JSON analysis
    const parsed = JSON.parse(analysisText);
    console.log('DEBUG: Successfully parsed JSON analysis:', parsed);
    setParsedAnalysis(parsed);
    
    setAnalyzing(false);
    console.log('DEBUG: Analysis completed successfully');
  };
  return (
    <div className="PaperCard">
      <h3>{paper.title}</h3>
      <p><strong>Authors:</strong> {paper.authors.join(', ')}</p>
      <p><strong>Categories:</strong> {paper.categories.join(', ')}</p>
      <p><strong>Published:</strong> {new Date(paper.published_date).toLocaleDateString()}</p>
      <p>{paper.abstract}</p>
      <div className="ActionButtons">
        {paper.pdf_url && (
          <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer">
            View PDF
          </a>
        )}
        <button onClick={handleAnalyze} disabled={analyzing}>
          {analyzing ? 'Analyzing...' : 'AI Analysis'}
        </button>
      </div>
      
      {analyzing && (
        <div className="AnalyzingSection">
          <p>🤖 AI 분석 중...</p>
        </div>
      )}
      
      {parsedAnalysis && (
        <div className="StructuredAnalysis">
          <div className="BackgroundSection">
            <h4>🎯 Background</h4>
            <p><strong>Problem:</strong> {parsedAnalysis.background?.problem_definition || 'Background information about the research problem, previous work, and motivation for this study will be displayed here.'}</p>
            <p><strong>Motivation:</strong> {parsedAnalysis.background?.motivation || 'Research motivation details...'}</p>
          </div>
          
          <div className="ContributionsSection">
            <h4>💡 Contributions</h4>
            <ul>
              {parsedAnalysis.contributions?.map((contrib, idx) => (
                <li key={idx}>{contrib}</li>
              )) || [
                <li key="default">Key contributions and novel aspects of this research will be summarized here.</li>
              ]}
            </ul>
          </div>
          
          <div className="MethodologySection">
            <h4>🔬 Methodology</h4>
            <p><strong>Approach:</strong> {parsedAnalysis.methodology?.approach || 'Description of the research methods, experimental setup, algorithms, or theoretical approaches used in this study.'}</p>
            <p><strong>Datasets:</strong> {parsedAnalysis.methodology?.datasets || 'Dataset information...'}</p>
          </div>
          
          {parsedAnalysis.results && (
            <div className="ResultsSection">
              <h4>📊 Results</h4>
              <p><strong>Key Findings:</strong> {parsedAnalysis.results.key_findings}</p>
              <p><strong>Performance:</strong> {parsedAnalysis.results.performance}</p>
            </div>
          )}
        </div>
      )}
      
      {analysis && !parsedAnalysis && (
        <div className="RawAnalysisSection">
          <h4>AI Analysis (Raw)</h4>
          <pre>{analysis}</pre>
        </div>
      )}
      
      {paper.structured_summary && (
        <div className="SummarySection">
          <h4>AI Summary</h4>
          <p><strong>Problem:</strong> {paper.structured_summary.background?.problem_definition}</p>
          <p><strong>Contributions:</strong> {paper.structured_summary.contributions?.join(', ')}</p>
        </div>
      )}
    </div>
  );
};

export default PaperCard;
