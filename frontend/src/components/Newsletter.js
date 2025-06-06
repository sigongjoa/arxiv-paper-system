import React, { useState } from 'react';
import { newsletterAPI } from '../utils/api';

const Newsletter = () => {
  const [config, setConfig] = useState({
    recipients: '',
    sender_email: '',
    domain: 'computer',
    days_back: 1,
    max_papers: 10,
    title: 'arXiv Newsletter'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const parseRecipients = (recipientString) => {
    return recipientString.split(',').map(email => email.trim()).filter(email => email);
  };

  const handleGenerate = async () => {
    const recipientList = parseRecipients(config.recipients);
    if (recipientList.length === 0) {
      setError('수신자 이메일을 입력하세요.');
      return;
    }
    if (!config.sender_email) {
      setError('발신자 이메일을 입력하세요.');
      return;
    }

    setLoading(true);
    try {
      const response = await newsletterAPI.create({
        ...config,
        recipients: recipientList
      });
      
      if (response.data.success) {
        alert(`뉴스레터가 성공적으로 전송되었습니다. (${response.data.papers_count}개 논문, ${response.data.recipients_count}명 수신자)`);
        setError('');
      } else {
        setError(response.data.error || '뉴스레터 생성 실패');
      }
    } catch (err) {
      setError('뉴스레터 생성 실패: ' + err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setLoading(true);
    try {
      const response = await newsletterAPI.test({
        domain: config.domain,
        max_papers: Math.min(config.max_papers, 5)
      });
      
      if (response.data.success) {
        const preview = response.data.papers_preview.map(p => 
          `- ${p.title} (${p.arxiv_id})`
        ).join('\n');
        alert(`테스트 성공!\n논문 ${response.data.papers_count}개 수집\n미리보기:\n${preview}`);
        setError('');
      } else {
        setError(response.data.error || '테스트 실패');
      }
    } catch (err) {
      setError('테스트 실패: ' + err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
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
                value={config.sender_email}
                onChange={(e) => setConfig({...config, sender_email: e.target.value})}
              />
            </div>
            <div className="FormGroup">
              <label className="FormLabel">연구 도메인</label>
              <select
                className="FormControl"
                value={config.domain}
                onChange={(e) => setConfig({...config, domain: e.target.value})}
              >
                <option value="computer">Computer Science</option>
                <option value="math">Mathematics</option>
                <option value="physics">Physics</option>
              </select>
            </div>
            <div className="FormGroup">
              <label className="FormLabel">기간 (일)</label>
              <input
                type="number"
                className="FormControl"
                value={config.days_back}
                onChange={(e) => setConfig({...config, days_back: parseInt(e.target.value)})}
                min="1"
              />
            </div>
            <div className="FormGroup">
              <label className="FormLabel">최대 논문 수</label>
              <input
                type="number"
                className="FormControl"
                value={config.max_papers}
                onChange={(e) => setConfig({...config, max_papers: parseInt(e.target.value)})}
                min="1"
                max="50"
              />
            </div>
          </div>

          <div className="FormGroup">
            <label className="FormLabel">뉴스레터 제목</label>
            <input
              type="text"
              className="FormControl"
              value={config.title}
              onChange={(e) => setConfig({...config, title: e.target.value})}
            />
          </div>

          <div style={{display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem'}}>
            <button
              className="Button Button--primary"
              onClick={handleGenerate}
              disabled={loading}
            >
              <i className="fas fa-envelope"></i> {loading ? '생성 중...' : '생성 & 전송'}
            </button>
            <button
              className="Button"
              style={{backgroundColor: 'transparent', border: '1px solid var(--border)', color: 'var(--text)'}}
              onClick={handleTest}
              disabled={loading}
            >
              <i className="fas fa-flask"></i> 테스트
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
              <i className="fas fa-file-pdf" style={{fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '1rem'}}></i>
              <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>PDF 생성</h3>
              <p>논문 목록과 요약을 PDF로 자동 생성</p>
            </div>
            <div style={{textAlign: 'center', padding: '1.5rem'}}>
              <i className="fas fa-envelope" style={{fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '1rem'}}></i>
              <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>이메일 전송</h3>
              <p>HTML 형식으로 자동 이메일 전송</p>
            </div>
            <div style={{textAlign: 'center', padding: '1.5rem'}}>
              <i className="fas fa-filter" style={{fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '1rem'}}></i>
              <h3 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem'}}>맞춤 필터</h3>
              <p>도메인, 카테고리별 필터링</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Newsletter;
