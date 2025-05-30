import React, { useState } from 'react';

const WebPDFViewer = () => {
  const [pdfList, setPdfList] = useState([]);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('latest');
  const [category, setCategory] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(100);

  const handleSearch = async () => {
    try {
      const response = await fetch('/api/pdfs/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          sortBy,
          category
        })
      });
      if (response.ok) {
        const data = await response.json();
        setPdfList(data);
      }
    } catch (err) {
      console.error('ERROR:', err);
    }
  };

  const handleUpload = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (file) {
        const formData = new FormData();
        formData.append('pdf', file);
        
        try {
          const response = await fetch('/api/pdfs/upload', {
            method: 'POST',
            body: formData
          });
          if (response.ok) {
            const data = await response.json();
            setPdfList(prev => [data, ...prev]);
          }
        } catch (err) {
          console.error('ERROR:', err);
        }
      }
    };
    input.click();
  };

  const handleSelectPdf = (pdf) => {
    setSelectedPdf(pdf);
    setCurrentPage(1);
    setTotalPages(pdf.totalPages || 1);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));
  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1));
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages));

  const handleDownload = () => {
    if (selectedPdf) {
      const a = document.createElement('a');
      a.href = selectedPdf.url;
      a.download = selectedPdf.title + '.pdf';
      a.click();
    }
  };

  const handlePrint = () => {
    if (selectedPdf) {
      window.open(selectedPdf.url, '_blank');
    }
  };

  const handleRotate = () => {
    // 회전 기능 구현
  };

  return (
    <div style={{display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', height: 'calc(100vh - 200px)'}}>
      <div style={{backgroundColor: 'white', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
        <div style={{padding: '1rem', backgroundColor: 'var(--secondary)', borderBottom: '1px solid var(--border)', fontWeight: 600}}>
          <i className="fas fa-list"></i> PDF 컬렉션 ({pdfList.length})
        </div>
        <div style={{flex: 1, overflowY: 'auto', padding: '1rem'}}>
          <div style={{display: 'flex', gap: '0.5rem', marginBottom: '1rem'}}>
            <input
              type="text"
              className="FormControl"
              placeholder="PDF 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{flex: 1}}
            />
            <button className="Button Button--primary" style={{padding: '0.5rem 1rem', fontSize: '0.875rem'}} onClick={handleSearch}>
              <i className="fas fa-search"></i>
            </button>
          </div>
          
          <div style={{marginBottom: '1rem'}}>
            <div style={{marginBottom: '0.75rem'}}>
              <label style={{display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', fontWeight: 500}}>정렬</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{width: '100%', padding: '0.5rem', border: '1px solid var(--border)', borderRadius: 'var(--radius)', fontSize: '0.875rem'}}
              >
                <option value="latest">최신순</option>
                <option value="title">제목순</option>
                <option value="author">저자순</option>
                <option value="date">날짜순</option>
              </select>
            </div>
            
            <div style={{marginBottom: '0.75rem'}}>
              <label style={{display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', fontWeight: 500}}>카테고리</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{width: '100%', padding: '0.5rem', border: '1px solid var(--border)', borderRadius: 'var(--radius)', fontSize: '0.875rem'}}
              >
                <option value="all">전체 카테고리</option>
                <option value="cs">Computer Science</option>
                <option value="math">Mathematics</option>
                <option value="physics">Physics</option>
              </select>
            </div>
          </div>
          
          <ul style={{listStyle: 'none'}}>
            {pdfList.map((pdf, index) => (
              <li
                key={index}
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
                <div style={{fontWeight: 500, marginBottom: '0.25rem', fontSize: '0.875rem'}}>{pdf.title}</div>
                <div style={{fontSize: '0.75rem', color: 'var(--text-light)'}}>{pdf.author} • {pdf.date}</div>
              </li>
            ))}
          </ul>
          
          {pdfList.length === 0 && (
            <div style={{textAlign: 'center', padding: '2rem 1rem'}}>
              <i className="fas fa-file-pdf" style={{fontSize: '2rem', marginBottom: '1rem', color: 'var(--border)'}}></i>
              <h4 style={{fontSize: '1rem', marginBottom: '0.5rem'}}>PDF를 찾을 수 없음</h4>
              <p style={{fontSize: '0.875rem', color: 'var(--text-light)'}}>PDF를 업로드하거나 논문을 검색하여 시작하세요.</p>
            </div>
          )}
        </div>
      </div>
      
      <div style={{backgroundColor: 'white', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
        <div style={{padding: '1rem', backgroundColor: 'var(--secondary)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{fontWeight: 600, fontSize: '1.125rem'}}>웹 PDF 뷰어</div>
          <div>
            <button className="Button Button--primary" style={{padding: '0.5rem 1rem', fontSize: '0.875rem'}} onClick={handleUpload}>
              <i className="fas fa-upload"></i> PDF 업로드
            </button>
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
              disabled={!selectedPdf}
              title="너비에 맞춤"
            >
              <i className="fas fa-arrows-alt-h"></i>
            </button>
            <button
              style={{background: 'transparent', border: 'none', padding: '0.5rem', cursor: 'pointer', borderRadius: 'var(--radius)', color: 'var(--text)', transition: 'background-color 0.2s ease'}}
              onClick={handleRotate}
              disabled={!selectedPdf}
              title="회전"
            >
              <i className="fas fa-redo"></i>
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
              <p>사이드바에서 PDF를 선택하거나 새 파일을 업로드하여 시작하세요.</p>
              <button className="Button Button--primary" style={{marginTop: '1rem'}} onClick={handleUpload}>
                <i className="fas fa-upload"></i> PDF 업로드
              </button>
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
                src={selectedPdf.url}
                style={{
                  width: `${zoom}%`,
                  height: '100%',
                  border: 'none',
                  maxWidth: '100%'
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
