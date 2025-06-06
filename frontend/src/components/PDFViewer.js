import React, { useState, useRef, useEffect } from 'react';

const PDFViewer = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfName, setPdfName] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    const handleLoadPdf = (event) => {
      console.log('DEBUG: PDF load event received:', event.detail);
      const { url, name, title } = event.detail;
      
      setPdfUrl(url);
      setPdfName(name || title || 'AI Analysis PDF');
      setPdfFile(null); // Clear file-based PDF
      setCurrentPage(1);
      setTotalPages(1);
      setError('');
      
      console.log('DEBUG: PDF loaded in viewer:', name);
    };
    
    window.addEventListener('loadPdf', handleLoadPdf);
    
    return () => {
      window.removeEventListener('loadPdf', handleLoadPdf);
    };
  }, []);
  
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
      setPdfUrl(null); // Clear URL-based PDF
      setPdfName(file.name);
      setCurrentPage(1);
      setTotalPages(1);
      setError('');
    } else {
      setError('PDF 파일만 업로드 가능합니다.');
    }
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));
  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1));
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages));

  const handleDownload = () => {
    if (pdfFile) {
      const url = URL.createObjectURL(pdfFile);
      const a = document.createElement('a');
      a.href = url;
      a.download = pdfFile.name;
      a.click();
      URL.revokeObjectURL(url);
    } else if (pdfUrl) {
      const a = document.createElement('a');
      a.href = pdfUrl;
      a.download = pdfName;
      a.click();
    }
  };

  const handlePrint = () => {
    if (pdfFile) {
      const url = URL.createObjectURL(pdfFile);
      window.open(url, '_blank');
    } else if (pdfUrl) {
      window.open(pdfUrl, '_blank');
    }
  };

  return (
    <div>
      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">PDF 뷰어</h2>
        </div>
        <div className="CardBody">
          <div style={{backgroundColor: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd', padding: '1rem', borderRadius: 'var(--radius)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
            <i className="fas fa-info-circle"></i>
            <div>
              <strong>PDF 파일 업로드</strong>
              <p>arXiv 논문이나 로컬 저장소의 PDF 파일을 업로드하여 확인하세요.</p>
            </div>
          </div>
          
          {error && <div className="Error">{error}</div>}
          
          <div
            style={{
              border: '2px dashed var(--border)',
              borderRadius: 'var(--radius)',
              padding: '3rem 2rem',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'border-color 0.2s ease',
              backgroundColor: '#fafafa'
            }}
            onClick={() => fileInputRef.current?.click()}
            onMouseEnter={(e) => e.target.style.borderColor = 'var(--primary)'}
            onMouseLeave={(e) => e.target.style.borderColor = 'var(--border)'}
          >
            <i className="fas fa-cloud-upload-alt" style={{fontSize: '3rem', color: 'var(--text-light)', marginBottom: '1rem'}}></i>
            <h3 style={{fontSize: '1.25rem', marginBottom: '0.5rem', color: 'var(--text)'}}>PDF 파일 업로드</h3>
            <p style={{color: 'var(--text-light)', marginBottom: '1rem'}}>클릭하거나 파일을 드래그하여 업로드</p>
            <button className="Button Button--primary">
              <i className="fas fa-upload"></i> 파일 선택
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              style={{display: 'none'}}
              onChange={handleFileUpload}
            />
          </div>
        </div>
      </div>
      
      <div style={{backgroundColor: 'white', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden', minHeight: '600px'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', backgroundColor: 'var(--secondary)', borderBottom: '1px solid var(--border)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handlePrevPage}
              disabled={(!pdfFile && !pdfUrl) || currentPage <= 1}
              title="이전 페이지"
            >
              <i className="fas fa-chevron-left"></i>
            </button>
            <span>페이지 {(pdfFile || pdfUrl) ? currentPage : '-'} / {(pdfFile || pdfUrl) ? totalPages : '-'}</span>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleNextPage}
              disabled={(!pdfFile && !pdfUrl) || currentPage >= totalPages}
              title="다음 페이지"
            >
              <i className="fas fa-chevron-right"></i>
            </button>
          </div>
          
          <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleZoomOut}
              disabled={!pdfFile && !pdfUrl}
              title="축소"
            >
              <i className="fas fa-search-minus"></i>
            </button>
            <span>{zoom}%</span>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleZoomIn}
              disabled={!pdfFile && !pdfUrl}
              title="확대"
            >
              <i className="fas fa-search-plus"></i>
            </button>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              disabled={!pdfFile && !pdfUrl}
              title="너비에 맞춤"
            >
              <i className="fas fa-arrows-alt-h"></i>
            </button>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleDownload}
              disabled={!pdfFile && !pdfUrl}
              title="다운로드"
            >
              <i className="fas fa-download"></i>
            </button>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handlePrint}
              disabled={!pdfFile && !pdfUrl}
              title="인쇄"
            >
              <i className="fas fa-print"></i>
            </button>
          </div>
        </div>
        
        <div style={{backgroundColor: '#f1f1f1', minHeight: '500px', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative'}}>
          {!pdfFile && !pdfUrl ? (
            <div style={{textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-light)'}}>
              <i className="fas fa-file-pdf" style={{fontSize: '4rem', marginBottom: '1rem', color: 'var(--border)'}}></i>
              <h3 style={{fontSize: '1.5rem', marginBottom: '1rem', fontWeight: 600}}>PDF가 로드되지 않음</h3>
              <p>AI 분석 후 PDF를 생성하거나 파일을 업로드하여 확인하세요</p>
            </div>
          ) : (
            <div style={{
              width: '100%',
              height: '500px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'white',
              border: '1px solid var(--border)'
            }}>
              <iframe
                src={pdfFile ? URL.createObjectURL(pdfFile) : pdfUrl}
                style={{
                  width: `${zoom}%`,
                  height: '100%',
                  border: 'none'
                }}
                title={`PDF Viewer - ${pdfName}`}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;
