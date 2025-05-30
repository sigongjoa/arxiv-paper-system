import React, { useState } from 'react';

const Newsletter = () => {
  const [config, setConfig] = useState({
    recipients: '',
    senderEmail: '',
    domain: 'cs',
    period: 7,
    maxPapers: 10,
    subject: 'arXiv Newsletter',
    template: 'basic'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const templates = [
    { id: 'basic', name: '기본 레이아웃', description: '간단하고 깔끔한 디자인' },
    { id: 'modern', name: '모던 레이아웃', description: '시각적 카테고리와 AI 인사이트' },
    { id: 'academic', name: '학술 레이아웃', description: '인용과 상세 메타데이터' }
  ];

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/newsletter/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (!response.ok) throw new Error('뉴스레터 생성 실패');
      alert('뉴스레터가 성공적으로 전송되었습니다.');
      setError('');
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    try {
      const response = await fetch('/api/newsletter/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (!response.ok) throw new Error('미리보기 생성 실패');
      const html = await response.text();
      const newWindow = window.open();
      newWindow.document.write(html);
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    }
  };

  return (
    <div>
      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">뉴스레터 자동화</h2>
        </div>
        <div className="CardBody">
          {error && <div className="Error">{error}</div>}
          
          <div className="FormGroup">
            <label className="FormLabel">수신자</label>
            <textarea
              className="FormControl"
              placeholder="email1@example.com, email2@example.com"
              value={config.recipients}
              onChange={(e) => setConfig({...config, recipients: e.target.value})}
              style={{minHeight: '80px'}}
            />
            <small style={{color: 'var(--text-light)', fontSize: '0.875rem'}}>
              쉼표로 구분된 이메일 주소
            </small>
          </div>

          <div className="Grid">
            <div className="FormGroup">
              <label className="FormLabel">발신자 이메일</label>
              <input
                type="email"
                className="FormControl"
                placeholder="newsletter@example.com"
                value={config.senderEmail}
                onChange={(e) => setConfig({...config, senderEmail: e.target.value})}
              />
            </div>
            <div className="FormGroup">
              <label className="FormLabel">연구 도메인</label>
              <select
                className="FormControl"
                value={config.domain}
                onChange={(e) => setConfig({...config, domain: e.target.value})}
              >
                <option value="cs">Computer Science</option>
                <option value="math">Mathematics</option>
                <option value="physics">Physics</option>
                <option value="q-bio">Quantitative Biology</option>
                <option value="q-fin">Quantitative Finance</option>
              </select>
            </div>
            <div className="FormGroup">
              <label className="FormLabel">기간 (일)</label>
              <input
                type="number"
                className="FormControl"
                value={config.period}
                onChange={(e) => setConfig({...config, period: parseInt(e.target.value)})}
                min="1"
              />
            </div>
            <div className="FormGroup">
              <label className="FormLabel">최대 논문 수</label>
              <input
                type="number"
                className="FormControl"
                value={config.maxPapers}
                onChange={(e) => setConfig({...config, maxPapers: parseInt(e.target.value)})}
                min="1"
                max="50"
              />
            </div>
          </div>

          <div className="FormGroup">
            <label className="FormLabel">이메일 제목</label>
            <input
              type="text"
              className="FormControl"
              value={config.subject}
              onChange={(e) => setConfig({...config, subject: e.target.value})}
            />
          </div>

          <div className="FormGroup">
            <label className="FormLabel">템플릿 선택</label>
            <div className="Grid">
              {templates.map(template => (
                <div
                  key={template.id}
                  className={`Card ${config.template === template.id ? 'selected' : ''}`}
                  style={{
                    cursor: 'pointer',
                    border: config.template === template.id ? '2px solid var(--primary)' : '1px solid var(--border-light)',
                    padding: '1rem'
                  }}
                  onClick={() => setConfig({...config, template: template.id})}
                >
                  <h4 style={{marginBottom: '0.5rem'}}>{template.name}</h4>
                  <p style={{color: 'var(--text-light)', fontSize: '0.875rem'}}>
                    {template.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div style={{display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem'}}>
            <button
              className="Button Button--primary"
              onClick={handleGenerate}
              disabled={loading || !config.recipients || !config.senderEmail}
            >
              <i className="fas fa-envelope"></i> {loading ? '생성 중...' : '생성 & 전송'}
            </button>
            <button
              className="Button"
              style={{backgroundColor: 'transparent', border: '1px solid var(--border)', color: 'var(--text)'}}
              onClick={handlePreview}
            >
              <i className="fas fa-eye"></i> 미리보기
            </button>
          </div>
        </div>
      </div>

      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">기능</h2>
        </div>
        <div className="CardBody">
          <div className="Grid">
            <div style={{textAlign: 'center', padding: '1.5rem'}}>
              <i className="fas fa-robot" style={{fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '1rem'}}></i>
              <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>AI 요약</h3>
              <p>고급 AI를 사용한 연구 논문 자동 요약</p>
            </div>
            <div style={{textAlign: 'center', padding: '1.5rem'}}>
              <i className="fas fa-calendar-alt" style={{fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '1rem'}}></i>
              <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>예약 발송</h3>
              <p>일간, 주간, 월간 뉴스레터 자동 발송</p>
            </div>
            <div style={{textAlign: 'center', padding: '1.5rem'}}>
              <i className="fas fa-filter" style={{fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '1rem'}}></i>
              <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>맞춤 필터</h3>
              <p>도메인, 카테고리, 저자별 필터링</p>
            </div>
            <div style={{textAlign: 'center', padding: '1.5rem'}}>
              <i className="fas fa-chart-bar" style={{fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '1rem'}}></i>
              <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>분석</h3>
              <p>열람률, 클릭률 등 참여 지표 추적</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Newsletter;
