import React, { useState } from 'react';

const MailingSend = () => {
  const [smtpConfig, setSmtpConfig] = useState({
    host: '',
    port: 587,
    username: '',
    password: '',
    senderEmail: '',
    senderName: ''
  });

  const [mailSettings, setMailSettings] = useState({
    recipients: '',
    domain: 'cs',
    period: 7,
    maxPapers: 10,
    subject: 'arXiv Newsletter'
  });

  const [sendStatus, setSendStatus] = useState({
    sent: 0,
    pending: 0,
    failed: 0,
    total: 0,
    progress: 0
  });

  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const parseRecipients = (recipientString) => {
    return recipientString.split(',').map(email => email.trim()).filter(email => email);
  };

  const handleSend = async () => {
    const recipientList = parseRecipients(mailSettings.recipients);
    if (recipientList.length === 0) {
      setError('수신자 목록을 입력하세요.');
      return;
    }

    setLoading(true);
    setSendStatus({
      sent: 0,
      pending: recipientList.length,
      failed: 0,
      total: recipientList.length,
      progress: 0
    });

    const recipientStatus = recipientList.map(email => ({
      email,
      status: 'pending'
    }));
    setRecipients(recipientStatus);

    try {
      const response = await fetch('/api/newsletter/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          smtp: smtpConfig,
          settings: mailSettings,
          recipients: recipientList
        })
      });

      if (!response.ok) throw new Error('뉴스레터 전송 실패');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
          try {
            const update = JSON.parse(line);
            if (update.type === 'progress') {
              setSendStatus(prev => ({
                ...prev,
                sent: update.sent,
                failed: update.failed,
                pending: update.total - update.sent - update.failed,
                progress: (update.sent + update.failed) / update.total * 100
              }));

              setRecipients(prev => prev.map(recipient => {
                const statusUpdate = update.recipients?.find(r => r.email === recipient.email);
                return statusUpdate ? { ...recipient, status: statusUpdate.status } : recipient;
              }));
            }
          } catch (e) {
            console.error('JSON 파싱 오류:', e);
          }
        }
      }

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
        body: JSON.stringify(mailSettings)
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
          <h2 className="CardTitle">뉴스레터 전송</h2>
        </div>
        <div className="CardBody">
          {error && <div className="Error">{error}</div>}
          
          <p style={{color: 'var(--text-light)', marginBottom: '1.5rem'}}>
            최신 arXiv 논문과 함께 구독자에게 뉴스레터를 구성하고 전송합니다.
          </p>
          
          <div className="Grid">
            <div className="Card" style={{marginBottom: 0}}>
              <div className="CardHeader">
                <h2 className="CardTitle">SMTP 설정</h2>
              </div>
              <div className="CardBody">
                <div className="FormGroup">
                  <label className="FormLabel">SMTP 호스트</label>
                  <input
                    type="text"
                    className="FormControl"
                    placeholder="smtp.gmail.com"
                    value={smtpConfig.host}
                    onChange={(e) => setSmtpConfig({...smtpConfig, host: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">포트</label>
                  <input
                    type="number"
                    className="FormControl"
                    placeholder="587"
                    value={smtpConfig.port}
                    onChange={(e) => setSmtpConfig({...smtpConfig, port: parseInt(e.target.value)})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">사용자명</label>
                  <input
                    type="email"
                    className="FormControl"
                    placeholder="your-email@gmail.com"
                    value={smtpConfig.username}
                    onChange={(e) => setSmtpConfig({...smtpConfig, username: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">비밀번호</label>
                  <input
                    type="password"
                    className="FormControl"
                    placeholder="•••••••••••••"
                    value={smtpConfig.password}
                    onChange={(e) => setSmtpConfig({...smtpConfig, password: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">발신자 이메일</label>
                  <input
                    type="email"
                    className="FormControl"
                    placeholder="newsletter@example.com"
                    value={smtpConfig.senderEmail}
                    onChange={(e) => setSmtpConfig({...smtpConfig, senderEmail: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">발신자 이름</label>
                  <input
                    type="text"
                    className="FormControl"
                    placeholder="arXiv Newsletter"
                    value={smtpConfig.senderName}
                    onChange={(e) => setSmtpConfig({...smtpConfig, senderName: e.target.value})}
                  />
                </div>
                
                <button className="Button Button--success">
                  <i className="fas fa-save"></i> 설정 저장
                </button>
              </div>
            </div>
            
            <div className="Card" style={{marginBottom: 0}}>
              <div className="CardHeader">
                <h2 className="CardTitle">뉴스레터 설정</h2>
              </div>
              <div className="CardBody">
                <div className="FormGroup">
                  <label className="FormLabel">수신자 (쉼표로 구분)</label>
                  <textarea
                    className="FormControl"
                    placeholder="email1@example.com, email2@example.com"
                    value={mailSettings.recipients}
                    onChange={(e) => setMailSettings({...mailSettings, recipients: e.target.value})}
                    style={{minHeight: '80px'}}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">도메인</label>
                  <select
                    className="FormControl"
                    value={mailSettings.domain}
                    onChange={(e) => setMailSettings({...mailSettings, domain: e.target.value})}
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
                    min="1"
                    value={mailSettings.period}
                    onChange={(e) => setMailSettings({...mailSettings, period: parseInt(e.target.value)})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">최대 논문 수</label>
                  <input
                    type="number"
                    className="FormControl"
                    min="1"
                    max="50"
                    value={mailSettings.maxPapers}
                    onChange={(e) => setMailSettings({...mailSettings, maxPapers: parseInt(e.target.value)})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">제목</label>
                  <input
                    type="text"
                    className="FormControl"
                    value={mailSettings.subject}
                    onChange={(e) => setMailSettings({...mailSettings, subject: e.target.value})}
                  />
                </div>
                
                <div style={{display: 'flex', gap: '1rem'}}>
                  <button className="Button Button--primary" onClick={handleSend} disabled={loading}>
                    <i className="fas fa-envelope"></i> 뉴스레터 전송
                  </button>
                  <button className="Button Button--danger" onClick={handlePreview}>
                    <i className="fas fa-eye"></i> 미리보기
                  </button>
                </div>
              </div>
            </div>
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
          
          <div style={{backgroundColor: 'var(--secondary)', borderRadius: 'var(--radius)', padding: '1rem', marginBottom: '1rem'}}>
            <h4 style={{marginBottom: '1rem'}}>수신자 상태</h4>
            {recipients.length > 0 ? (
              recipients.map((recipient, index) => (
                <div key={index} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: index < recipients.length - 1 ? '1px solid var(--border-light)' : 'none'}}>
                  <div style={{fontWeight: 500}}>{recipient.email}</div>
                  <div>
                    <span style={{
                      fontSize: '0.875rem',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '9999px',
                      backgroundColor: recipient.status === 'sent' ? '#d1fae5' : recipient.status === 'failed' ? '#fee2e2' : '#fef3c7',
                      color: recipient.status === 'sent' ? '#065f46' : recipient.status === 'failed' ? '#b91c1c' : '#92400e'
                    }}>
                      {recipient.status === 'sent' ? '전송됨' : recipient.status === 'failed' ? '실패' : '대기 중'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div style={{textAlign: 'center', color: 'var(--text-light)', padding: '2rem'}}>
                수신자가 설정되지 않았습니다. 이메일 주소를 추가하여 시작하세요.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MailingSend;
