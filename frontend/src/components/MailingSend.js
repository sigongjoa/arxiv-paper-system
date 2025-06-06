import React, { useState } from 'react';
import { newsletterAPI } from '../utils/api';

const MailingSend = () => {
  const [config, setConfig] = useState({
    recipients: '',
    sender_email: '',
    domain: 'computer',
    days_back: 1,
    max_papers: 10,
    title: 'arXiv Newsletter'
  });

  const [sendStatus, setSendStatus] = useState({
    sent: 0,
    pending: 0,
    failed: 0,
    total: 0,
    progress: 0
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const parseRecipients = (recipientString) => {
    return recipientString.split(',').map(email => email.trim()).filter(email => email);
  };

  const handleSend = async () => {
    const recipientList = parseRecipients(config.recipients);
    if (recipientList.length === 0) {
      setError('수신자 목록을 입력하세요.');
      return;
    }
    if (!config.sender_email) {
      setError('발신자 이메일을 입력하세요.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setSendStatus({
      sent: 0,
      pending: recipientList.length,
      failed: 0,
      total: recipientList.length,
      progress: 0
    });

    try {
      const response = await newsletterAPI.create({
        ...config,
        recipients: recipientList
      });

      if (response.data.success) {
        setResult(response.data);
        setSendStatus({
          sent: response.data.recipients_count || recipientList.length,
          pending: 0,
          failed: 0,
          total: recipientList.length,
          progress: 100
        });
        setError('');
      } else {
        setError(response.data.error || '뉴스레터 전송 실패');
        setSendStatus(prev => ({
          ...prev,
          failed: prev.total,
          pending: 0,
          progress: 100
        }));
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message;
      setError('뉴스레터 전송 실패: ' + errorMsg);
      setSendStatus(prev => ({
        ...prev,
        failed: prev.total,
        pending: 0,
        progress: 100
      }));
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setLoading(true);
    setError('');
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

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div>
      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">뉴스레터 전송</h2>
        </div>
        <div className="CardBody">
          {error && <div className="Error">{error}</div>}
          {result && (
            <div style={{backgroundColor: '#ecfdf5', color: 'var(--success)', border: '1px solid #d1fae5', padding: '1rem', borderRadius: 'var(--radius)', marginBottom: '1.5rem'}}>
              뉴스레터가 성공적으로 전송되었습니다! (논문 {result.papers_count}개, PDF {formatFileSize(result.pdf_size)}, 수신자 {result.recipients_count}명)
            </div>
          )}
          
          <p style={{color: 'var(--text-light)', marginBottom: '1.5rem'}}>
            최신 arXiv 논문과 함께 구독자에게 뉴스레터를 구성하고 전송합니다.
          </p>
          
          <div className="FormGroup">
            <label className="FormLabel">수신자 (쉼표로 구분)</label>
            <textarea
              className="FormControl"
              placeholder="email1@example.com, email2@example.com"
              value={config.recipients}
              onChange={(e) => setConfig({...config, recipients: e.target.value})}
              style={{minHeight: '80px'}}
            />
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
              <label className="FormLabel">도메인</label>
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
                min="1"
                value={config.days_back}
                onChange={(e) => setConfig({...config, days_back: parseInt(e.target.value)})}
              />
            </div>
            <div className="FormGroup">
              <label className="FormLabel">최대 논문 수</label>
              <input
                type="number"
                className="FormControl"
                min="1"
                max="50"
                value={config.max_papers}
                onChange={(e) => setConfig({...config, max_papers: parseInt(e.target.value)})}
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
          
          <div style={{display: 'flex', gap: '1rem', justifyContent: 'center'}}>
            <button 
              className="Button Button--primary" 
              onClick={handleSend} 
              disabled={loading}
            >
              <i className="fas fa-envelope"></i> {loading ? '전송 중...' : '뉴스레터 전송'}
            </button>
            <button 
              className="Button Button--danger" 
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
          <h2 className="CardTitle">전송 상태</h2>
        </div>
        <div className="CardBody">
          <div className="Grid">
            <div style={{border: '1px solid var(--border-light)', borderRadius: 'var(--radius)', padding: '1rem', textAlign: 'center'}}>
              <div style={{fontSize: '2rem', marginBottom: '0.5rem', color: 'var(--success)'}}>
                <i className="fas fa-check-circle"></i>
              </div>
              <div style={{fontWeight: 600, marginBottom: '0.25rem'}}>전송 완료</div>
              <div style={{fontSize: '0.875rem', color: 'var(--text-light)'}}>
                {sendStatus.sent} / {sendStatus.total}
              </div>
            </div>
            
            <div style={{border: '1px solid var(--border-light)', borderRadius: 'var(--radius)', padding: '1rem', textAlign: 'center'}}>
              <div style={{fontSize: '2rem', marginBottom: '0.5rem', color: 'var(--warning)'}}>
                <i className="fas fa-clock"></i>
              </div>
              <div style={{fontWeight: 600, marginBottom: '0.25rem'}}>대기 중</div>
              <div style={{fontSize: '0.875rem', color: 'var(--text-light)'}}>
                {sendStatus.pending}개
              </div>
            </div>
            
            <div style={{border: '1px solid var(--border-light)', borderRadius: 'var(--radius)', padding: '1rem', textAlign: 'center'}}>
              <div style={{fontSize: '2rem', marginBottom: '0.5rem', color: 'var(--danger)'}}>
                <i className="fas fa-exclamation-triangle"></i>
              </div>
              <div style={{fontWeight: 600, marginBottom: '0.25rem'}}>실패</div>
              <div style={{fontSize: '0.875rem', color: 'var(--text-light)'}}>
                {sendStatus.failed}개
              </div>
            </div>
          </div>
          
          <div style={{backgroundColor: 'var(--border-light)', borderRadius: '9999px', overflow: 'hidden', height: '0.5rem', margin: '1rem 0'}}>
            <div
              style={{
                backgroundColor: 'var(--success)',
                height: '100%',
                transition: 'width 0.3s ease',
                width: `${sendStatus.progress}%`
              }}
            />
          </div>
          
          <div style={{backgroundColor: 'var(--secondary)', borderRadius: 'var(--radius)', padding: '1rem'}}>
            <h4 style={{marginBottom: '1rem'}}>전송 결과</h4>
            {result ? (
              <div>
                <div style={{marginBottom: '0.5rem'}}>
                  <strong>성공적으로 전송됨:</strong> {result.recipients_count}명
                </div>
                <div style={{marginBottom: '0.5rem'}}>
                  <strong>논문 수:</strong> {result.papers_count}개
                </div>
                <div style={{marginBottom: '0.5rem'}}>
                  <strong>PDF 크기:</strong> {formatFileSize(result.pdf_size)}
                </div>
                {result.message_id && (
                  <div style={{fontSize: '0.875rem', color: 'var(--text-light)'}}>
                    메시지 ID: {result.message_id}
                  </div>
                )}
              </div>
            ) : (
              <div style={{textAlign: 'center', color: 'var(--text-light)', padding: '2rem'}}>
                뉴스레터를 전송하면 결과가 여기에 표시됩니다.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MailingSend;
