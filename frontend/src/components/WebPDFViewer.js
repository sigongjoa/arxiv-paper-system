import React, { useState, useEffect } from 'react';
import { pdfAPI } from '../utils/api';

const WebPDFViewer = () => {
  const [pdfList, setPdfList] = useState([]);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    loadPdfList();
  }, []);

  const loadPdfList = async () => {
    setLoading(true);
    try {
      const response = await pdfAPI.getList();
      if (response.data.success) {
        setPdfList(response.data.pdfs || []);
        setError('');
      } else {
        setError(response.data.error || 'PDF 목록 로드 실패');
      }
    } catch (err) {
      setError('PDF 목록 로드 실패: ' + err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPdf = async (pdf) => {
    setSelectedPdf(pdf);
    setCurrentPage(1);
    setTotalPages(1);
    setError('');
  };

  const handleDeletePdf = async (pdfId) => {
    if (!confirm('이 PDF를 삭제하시겠습니까?')) return;
    
    try {
      const response = await pdfAPI.delete(pdfId);
      if (response.data.success) {
        setPdfList(prev => prev.filter(pdf => pdf.id !== pdfId));
        if (selectedPdf?.id === pdfId) {
          setSelectedPdf(null);
        }
        alert('PDF가 삭제되었습니다.');
      } else {
        setError(response.data.error || 'PDF 삭제 실패');
      }
    } catch (err) {
      setError('PDF 삭제 실패: ' + err.message);
      console.error('ERROR:', err);
    }
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));
  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1));
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages));

  const handleDownload = async () => {
    if (!selectedPdf) return;
    
    try {
      const response = await pdfAPI.download(selectedPdf.id);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = selectedPdf.name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('다운로드 실패: ' + err.message);
      console.error('ERROR:', err);
    }
  };

  const handlePrint = async () => {
    if (!selectedPdf) return;
    
    try {
      const response = await pdfAPI.view(selectedPdf.id);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('프린트 실패: ' + err.message);
      console.error('ERROR:', err);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  return (
    <div style={{display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', height: 'calc(100vh - 200px)'}}>
      <div style={{backgroundColor: 'white', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
        <div style={{padding: '1rem', backgroundColor: 'var(--secondary)', borderBottom: '1px solid var(--border)', fontWeight: 600}}>
          <i className="fas fa-list"></i> PDF 컬렉션 ({pdfList.length})
        </div>
        <div style={{flex: 1, overflowY: 'auto', padding: '1rem'}}>
          {error && <div className="Error" style={{fontSize: '0.875rem', padding: '0.5rem', marginBottom: '1rem'}}>{error}</div>}
          
          <button
            className="Button Button--primary"
            style={{width: '100%', marginBottom: '1rem'}}
            onClick={loadPdfList}
            disabled={loading}
          >
            <i className="fas fa-refresh"></i> {loading ? '로딩 중...' : '새로고침'}
          </button>
          
          <ul style={{listStyle: 'none'}}>
            {pdfList.map((pdf) => (
              <li
                key={pdf.id}
                style={{
                  padding: '0.75rem',
                  borderBottom: '1px solid var(--border-light)',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease',
                  backgroundColor: selectedPdf?.id === pdf.id ? '#e0f2fe' : 'transparent',
                  borderLeft: selectedPdf?.id === pdf.id ? '3px solid var(--primary)' : 'none'
                }}
                onClick={() => handleSelectPdf(pdf)}
                onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--secondary)'}
                onMouseLeave={(e) => e.target.style.backgroundColor = selectedPdf?.id === pdf.id ? '#e0f2fe' : 'transparent'}
              >
                <div style={{fontWeight: 500, marginBottom: '0.25rem', fontSize: '0.875rem'}}>{pdf.name}</div>
                <div style={{fontSize: '0.75rem', color: 'var(--text-light)', marginBottom: '0.25rem'}}>
                  {formatFileSize(pdf.size)} • {formatDate(pdf.created_at)}
                </div>
                <button
                  className="Button Button--danger"
                  style={{padding: '0.25rem 0.5rem', fontSize: '0.75rem'}}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeletePdf(pdf.id);
                  }}
                >
                  <i className="fas fa-trash"></i> 삭제
                </button>
              </li>
            ))}
          </ul>
          
          {pdfList.length === 0 && !loading && (
            <div style={{textAlign: 'center', padding: '2rem 1rem'}}>
              <i className="fas fa-file-pdf" style={{fontSize: '2rem', marginBottom: '1rem', color: 'var(--border)'}}></i>
              <h4 style={{fontSize: '1rem', marginBottom: '0.5rem'}}>PDF를 찾을 수 없음</h4>
              <p style={{fontSize: '0.875rem', color: 'var(--text-light)'}}>뉴스레터를 생성하면 PDF가 자동으로 생성됩니다.</p>
            </div>
          )}
        </div>
      </div>
      
      <div style={{backgroundColor: 'white', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
        <div style={{padding: '1rem', backgroundColor: 'var(--secondary)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{fontWeight: 600, fontSize: '1.125rem'}}>
            {selectedPdf ? selectedPdf.name : '웹 PDF 뷰어'}
          </div>
        </div>
        
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', backgroundColor: '#fafafa', borderBottom: '1px solid var(--border)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handlePrevPage}
              disabled={!selectedPdf || currentPage <= 1}
              title="이전 페이지"
            >
              <i className="fas fa-chevron-left"></i>
            </button>
            <span>페이지 {selectedPdf ? currentPage : '-'} / {selectedPdf ? totalPages : '-'}</span>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleNextPage}
              disabled={!selectedPdf || currentPage >= totalPages}
              title="다음 페이지"
            >
              <i className="fas fa-chevron-right"></i>
            </button>
          </div>
          
          <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleZoomOut}
              disabled={!selectedPdf}
              title="축소"
            >
              <i className="fas fa-search-minus"></i>
            </button>
            <span>{zoom}%</span>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleZoomIn}
              disabled={!selectedPdf}
              title="확대"
            >
              <i className="fas fa-search-plus"></i>
            </button>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleDownload}
              disabled={!selectedPdf}
              title="다운로드"
            >
              <i className="fas fa-download"></i>
            </button>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handlePrint}
              disabled={!selectedPdf}
              title="인쇄"
            >
              <i className="fas fa-print"></i>
            </button>
          </div>
        </div>
        
        <div style={{flex: 1, backgroundColor: '#f1f1f1', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'auto'}}>
          {!selectedPdf ? (
            <div style={{textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-light)'}}>
              <i className="fas fa-file-pdf" style={{fontSize: '4rem', marginBottom: '1rem', color: 'var(--border)'}}></i>
              <h3 style={{fontSize: '1.5rem', marginBottom: '1rem', fontWeight: 600}}>PDF를 선택하여 보기</h3>
              <p>사이드바에서 PDF를 선택하여 시작하세요.</p>
            </div>
          ) : (
            <div style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'white'
            }}>
              <iframe
                src={`http://localhost:8000/api/v1/pdf/view/${selectedPdf.id}#zoom=${zoom}`}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none'
                }}
                title="PDF Viewer"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebPDFViewer;
