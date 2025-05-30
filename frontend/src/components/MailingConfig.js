import React, { useState, useEffect } from 'react';

const MailingConfig = () => {
  const [smtpConfig, setSmtpConfig] = useState({
    host: '',
    port: 587,
    username: '',
    password: '',
    security: 'tls'
  });
  
  const [senderInfo, setSenderInfo] = useState({
    email: '',
    name: '',
    replyTo: '',
    testEmail: ''
  });

  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadConfig();
    loadTemplates();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/config/smtp');
      if (response.ok) {
        const data = await response.json();
        setSmtpConfig(data.smtp || smtpConfig);
        setSenderInfo(data.sender || senderInfo);
      }
    } catch (err) {
      console.error('ERROR:', err);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('ERROR:', err);
    }
  };

  const saveSmtpConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/smtp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(smtpConfig)
      });
      if (!response.ok) throw new Error('SMTP 설정 저장 실패');
      alert('SMTP 설정이 저장되었습니다.');
      setError('');
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveSenderInfo = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/sender', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(senderInfo)
      });
      if (!response.ok) throw new Error('발신자 정보 저장 실패');
      alert('발신자 정보가 저장되었습니다.');
      setError('');
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async () => {
    if (!senderInfo.testEmail) {
      setError('테스트 이메일 주소를 입력하세요.');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch('/api/config/test-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: senderInfo.testEmail })
      });
      if (!response.ok) throw new Error('테스트 이메일 전송 실패');
      alert('테스트 이메일이 전송되었습니다.');
      setError('');
    } catch (err) {
      setError(err.message);
      console.error('ERROR:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">메일링 설정</h2>
        </div>
        <div className="CardBody">
          {error && <div className="Error">{error}</div>}
          
          <div style={{backgroundColor: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd', padding: '1rem', borderRadius: 'var(--radius)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
            <i className="fas fa-info-circle"></i>
            <div>
              <strong>SMTP 설정 필요</strong>
              <p>이메일 전송 기능을 활성화하려면 SMTP 서버 정보와 발신자 정보를 설정하세요.</p>
            </div>
          </div>
          
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
                  <label className="FormLabel">SMTP 포트</label>
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
                  <label className="FormLabel">보안 유형</label>
                  <select
                    className="FormControl"
                    value={smtpConfig.security}
                    onChange={(e) => setSmtpConfig({...smtpConfig, security: e.target.value})}
                  >
                    <option value="tls">TLS</option>
                    <option value="ssl">SSL</option>
                    <option value="starttls">STARTTLS</option>
                    <option value="none">없음</option>
                  </select>
                </div>
                
                <button className="Button Button--success" onClick={saveSmtpConfig} disabled={loading}>
                  <i className="fas fa-save"></i> 설정 저장
                </button>
              </div>
            </div>
            
            <div className="Card" style={{marginBottom: 0}}>
              <div className="CardHeader">
                <h2 className="CardTitle">발신자 정보</h2>
              </div>
              <div className="CardBody">
                <div className="FormGroup">
                  <label className="FormLabel">발신자 이메일</label>
                  <input
                    type="email"
                    className="FormControl"
                    placeholder="newsletter@example.com"
                    value={senderInfo.email}
                    onChange={(e) => setSenderInfo({...senderInfo, email: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">발신자 이름</label>
                  <input
                    type="text"
                    className="FormControl"
                    placeholder="arXiv Newsletter"
                    value={senderInfo.name}
                    onChange={(e) => setSenderInfo({...senderInfo, name: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">답장 이메일</label>
                  <input
                    type="email"
                    className="FormControl"
                    placeholder="support@example.com"
                    value={senderInfo.replyTo}
                    onChange={(e) => setSenderInfo({...senderInfo, replyTo: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">테스트 이메일</label>
                  <input
                    type="email"
                    className="FormControl"
                    placeholder="test@example.com"
                    value={senderInfo.testEmail}
                    onChange={(e) => setSenderInfo({...senderInfo, testEmail: e.target.value})}
                  />
                </div>
                
                <div style={{display: 'flex', gap: '1rem'}}>
                  <button className="Button Button--primary" onClick={saveSenderInfo} disabled={loading}>
                    <i className="fas fa-save"></i> 정보 저장
                  </button>
                  <button className="Button Button--warning" onClick={sendTestEmail} disabled={loading}>
                    <i className="fas fa-paper-plane"></i> 테스트 발송
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">이메일 템플릿</h2>
        </div>
        <div className="CardBody">
          <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: '1.5rem'}}>
            <button className="Button Button--primary">
              <i className="fas fa-plus"></i> 새 템플릿 생성
            </button>
          </div>
          
          <table style={{width: '100%', borderCollapse: 'collapse'}}>
            <thead>
              <tr style={{borderBottom: '2px solid var(--border)', textAlign: 'left'}}>
                <th style={{padding: '1rem'}}>템플릿 이름</th>
                <th style={{padding: '1rem'}}>수정일</th>
                <th style={{padding: '1rem'}}>상태</th>
                <th style={{padding: '1rem'}}>작업</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{borderBottom: '1px solid var(--border-light)'}}>
                <td style={{padding: '1rem'}}>기본 뉴스레터</td>
                <td style={{padding: '1rem'}}>2025-05-25</td>
                <td style={{padding: '1rem'}}>
                  <span style={{backgroundColor: '#d1fae5', color: '#065f46', padding: '0.25rem 0.5rem', fontSize: '0.75rem', fontWeight: 500, borderRadius: '9999px'}}>
                    활성
                  </span>
                </td>
                <td style={{padding: '1rem'}}>
                  <button className="Button Button--primary" style={{padding: '0.5rem', fontSize: '0.875rem', marginRight: '0.5rem'}}>편집</button>
                  <button className="Button Button--warning" style={{padding: '0.5rem', fontSize: '0.875rem'}}>복제</button>
                </td>
              </tr>
              <tr style={{borderBottom: '1px solid var(--border-light)'}}>
                <td style={{padding: '1rem'}}>월간 다이제스트</td>
                <td style={{padding: '1rem'}}>2025-05-20</td>
                <td style={{padding: '1rem'}}>
                  <span style={{backgroundColor: '#d1fae5', color: '#065f46', padding: '0.25rem 0.5rem', fontSize: '0.75rem', fontWeight: 500, borderRadius: '9999px'}}>
                    활성
                  </span>
                </td>
                <td style={{padding: '1rem'}}>
                  <button className="Button Button--primary" style={{padding: '0.5rem', fontSize: '0.875rem', marginRight: '0.5rem'}}>편집</button>
                  <button className="Button Button--warning" style={{padding: '0.5rem', fontSize: '0.875rem'}}>복제</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MailingConfig;
