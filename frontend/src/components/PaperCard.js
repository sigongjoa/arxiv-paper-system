import React, { useState, useEffect } from 'react';
import { paperAPI } from '../utils/api';

const PaperCard = ({ paper }) => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [progressStep, setProgressStep] = useState(0);
  
  const progressSteps = [
    { text: '📄 논문 내용 분석 준비 중...', icon: '📄' },
    { text: '🧠 AI 분석 엔진 시작...', icon: '🧠' },
    { text: '📝 분석 결과 생성 중...', icon: '📝' },
    { text: '📊 PDF 레이아웃 작성 중...', icon: '📊' },
    { text: '✨ 완료 및 PDF 로드 중...', icon: '✨' }
  ];
  
  useEffect(() => {
    let interval;
    if (analyzing) {
      setProgressStep(0);
      interval = setInterval(() => {
        setProgressStep(prev => {
          if (prev < progressSteps.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [analyzing]);
  
  const handleAnalyze = async () => {
    console.log('DEBUG: Starting analysis for paper:', paper.paper_id);
    setAnalyzing(true);
    setProgressStep(0);
    
    try {
      // 진행상태 표시를 위한 인위적 지연
      await new Promise(resolve => setTimeout(resolve, 1000));
      setProgressStep(1);
      
      const response = await paperAPI.analyzePaper(paper.paper_id);
      console.log('DEBUG: Analysis response:', response.data);
      
      setProgressStep(2);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const analysisText = response.data.analysis_result;
      setAnalysis(analysisText);
      
      setProgressStep(3);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // 팝업 대신 즉시 PDF 생성
      await generatePdfFromAnalysis(analysisText);
      
    } catch (error) {
      console.error('ERROR: Analysis failed:', error);
      alert('분석에 실패했습니다.');
    }
    
    setAnalyzing(false);
    setProgressStep(0);
  };
  
  const generatePdfFromAnalysis = async (analysisData) => {
    console.log('DEBUG: Auto-generating PDF for analysis:', paper.paper_id);
    
    // PDF 생성 단계로 업데이트
    setProgressStep(4);
    
    try {
      const response = await fetch('/api/v1/pdf/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          external_id: paper.paper_id,
          title: paper.title,
          analysis: analysisData
        })
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // PDF 뷰어에 자동으로 로드
        const event = new CustomEvent('loadPdf', { 
          detail: { 
            url: url, 
            name: `analysis_${paper.platform}_${paper.paper_id.replace('/', '_').replace('.', '_')}.pdf`,
            title: paper.title
          } 
        });
        window.dispatchEvent(event);
        
        console.log('DEBUG: PDF auto-generated and loaded');
        
        // PDF 뷰어 탭으로 자동 전환
        const pdfTab = document.querySelector('[data-tab="pdf-viewer"]');
        if (pdfTab) {
          pdfTab.click();
        }
        
      } else {
        throw new Error('PDF 생성 실패');
      }
    } catch (error) {
      console.error('ERROR: Auto PDF generation failed:', error);
      alert('PDF 생성에 실패했습니다.');
    }
  };

  return (
    <div className="PaperCard">
      <h3 className="PaperTitle">{paper.title}</h3>
      <div className="PaperMeta">
        <p><strong>저자:</strong> {Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors}</p>
        <p><strong>카테고리:</strong> {Array.isArray(paper.categories) ? paper.categories.join(', ') : paper.categories}</p>
        <p><strong>ID:</strong> {paper.paper_id} | <strong>Platform:</strong> {paper.platform}</p>
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
          {analyzing ? '🤖 분석 중... PDF 생성 중...' : '🧠 AI 분석 → PDF 생성'}
        </button>
      </div>
      
      {analyzing && (
        <div className="AnalyzingSection">
          <div className="LoadingSpinner">
            <div className="Spinner"></div>
            <p>🤖 AI가 논문을 분석하고 PDF를 생성하고 있습니다...</p>
            <div className="ProgressText">
              {progressSteps[progressStep]?.text}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaperCard;
