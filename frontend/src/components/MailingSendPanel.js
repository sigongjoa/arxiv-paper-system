import React, { useState, useEffect } from 'react';

const MailingSendPanel = () => {
  const [config, setConfig] = useState({
    smtpHost: '',
    smtpPort: 587,
    smtpUser: '',
    smtpPassword: '',
    fromEmail: '',
    fromName: ''
  });
  const [sendData, setSendData] = useState({
    recipients: '',
    domain: 'computer',
    daysBack: 1,
    maxPapers: 10,
    title: 'arXiv Newsletter'
  });
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);

  console.log('[DEBUG] MailingSendPanel initialized');

  const handleConfigChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: value }));
    console.log(`[DEBUG] Config updated: ${name} = ${value}`);
  };

  const handleSendDataChange = (e) => {
    const { name, value } = e.target;
    setSendData(prev => ({ ...prev, [name]: value }));
    console.log(`[DEBUG] SendData updated: ${name} = ${value}`);
  };

  const saveConfig = async () => {
    setLoading(true);
    setStatus('saving');
    console.log('[DEBUG] Saving config:', config);
    
    try {
      const response = await fetch('/api/v1/mailing/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      const data = await response.json();
      setStatus(data.success ? 'config_saved' : 'config_error');
      console.log('[DEBUG] Config save result:', data);
    } catch (error) {
      console.error('[ERROR] Config save failed:', error);
      setStatus('config_error');
    }
    
    setLoading(false);
  };

  const testNewsletter = async () => {
    setLoading(true);
    setStatus('testing');
    console.log('[DEBUG] Testing newsletter generation');
    
    try {
      const response = await fetch('/api/v1/newsletter/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: sendData.domain,
          max_papers: Math.min(sendData.maxPapers, 5)
        })
      });
      
      const data = await response.json();
      setResult(data);
      setStatus(data.success ? 'test_success' : 'test_failed');
      console.log('[DEBUG] Newsletter test result:', data);
    } catch (error) {
      console.error('[ERROR] Newsletter test failed:', error);
      setStatus('test_failed');
    }
    
    setLoading(false);
  };

  const sendNewsletter = async () => {
    setLoading(true);
    setStatus('sending');
    console.log('[DEBUG] Sending newsletter');
    
    const recipients = sendData.recipients.split(',').map(email => email.trim()).filter(email => email);
    
    try {
      const response = await fetch('/api/v1/newsletter/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipients: recipients,
          domain: sendData.domain,
          days_back: sendData.daysBack,
          max_papers: sendData.maxPapers,
          sender_email: config.fromEmail,
          title: sendData.title
        })
      });
      
      const data = await response.json();
      setResult(data);
      setStatus(data.success ? 'send_success' : 'send_failed');
      console.log('[DEBUG] Newsletter send result:', data);
    } catch (error) {
      console.error('[ERROR] Newsletter send failed:', error);
      setStatus('send_failed');
    }
    
    setLoading(false);
  };

  const loadConfig = async () => {
    console.log('[DEBUG] Loading config');
    try {
      const response = await fetch('/api/v1/mailing/config');
      const data = await response.json();
      if (data.success) {
        setConfig(data.config);
        console.log('[DEBUG] Config loaded');
      }
    } catch (error) {
      console.error('[ERROR] Config load failed:', error);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  return (
    <div className="MailingSendPanel">
      <div className="PanelHeader">
        <h1>뉴스레터 발송</h1>
        <p>메일링 설정 및 뉴스레터 생성/전송</p>
      </div>

      <div className="PanelGrid">
        <div className="ConfigSection">
          <h2>SMTP 설정</h2>
          <div className="FormGroup">
            <label>SMTP 호스트</label>
            <input
              type="text"
              name="smtpHost"
              value={config.smtpHost}
              onChange={handleConfigChange}
              placeholder="smtp.gmail.com"
            />
          </div>
          
          <div className="FormGroup">
            <label>포트</label>
            <input
              type="number"
              name="smtpPort"
              value={config.smtpPort}
              onChange={handleConfigChange}
            />
          </div>
          
          <div className="FormGroup">
            <label>사용자명</label>
            <input
              type="text"
              name="smtpUser"
              value={config.smtpUser}
              onChange={handleConfigChange}
            />
          </div>
          
          <div className="FormGroup">
            <label>비밀번호</label>
            <input
              type="password"
              name="smtpPassword"
              value={config.smtpPassword}
              onChange={handleConfigChange}
            />
          </div>
          
          <div className="FormGroup">
            <label>발신자 이메일</label>
            <input
              type="email"
              name="fromEmail"
              value={config.fromEmail}
              onChange={handleConfigChange}
            />
          </div>
          
          <div className="FormGroup">
            <label>발신자명</label>
            <input
              type="text"
              name="fromName"
              value={config.fromName}
              onChange={handleConfigChange}
            />
          </div>
          
          <button onClick={saveConfig} disabled={loading} className="SaveButton">
            {loading && status === 'saving' ? '저장 중...' : '설정 저장'}
          </button>
        </div>

        <div className="SendSection">
          <h2>뉴스레터 발송</h2>
          <div className="FormGroup">
            <label>수신자 이메일 (쉼표로 구분)</label>
            <textarea
              name="recipients"
              value={sendData.recipients}
              onChange={handleSendDataChange}
              placeholder="email1@example.com, email2@example.com"
              rows="3"
            />
          </div>
          
          <div className="FormGroup">
            <label>도메인</label>
            <select name="domain" value={sendData.domain} onChange={handleSendDataChange}>
              <option value="computer">컴퓨터과학</option>
              <option value="math">수학</option>
              <option value="physics">물리학</option>
              <option value="all">전체</option>
            </select>
          </div>
          
          <div className="FormGroup">
            <label>기간 (일)</label>
            <input
              type="number"
              name="daysBack"
              value={sendData.daysBack}
              onChange={handleSendDataChange}
              min="1"
              max="30"
            />
          </div>
          
          <div className="FormGroup">
            <label>최대 논문 수</label>
            <input
              type="number"
              name="maxPapers"
              value={sendData.maxPapers}
              onChange={handleSendDataChange}
              min="1"
              max="50"
            />
          </div>
          
          <div className="FormGroup">
            <label>제목</label>
            <input
              type="text"
              name="title"
              value={sendData.title}
              onChange={handleSendDataChange}
            />
          </div>
          
          <div className="ActionButtons">
            <button onClick={testNewsletter} disabled={loading} className="TestButton">
              {loading && status === 'testing' ? '테스트 중...' : '뉴스레터 테스트'}
            </button>
            
            <button 
              onClick={sendNewsletter} 
              disabled={loading || !sendData.recipients}
              className="SendButton"
            >
              {loading && status === 'sending' ? '발송 중...' : '뉴스레터 발송'}
            </button>
          </div>
        </div>
      </div>

      {status !== 'idle' && (
        <div className={`StatusResult ${status}`}>
          {status === 'config_saved' && '✅ 설정 저장됨'}
          {status === 'config_error' && '❌ 설정 저장 실패'}
          {status === 'test_success' && '✅ 테스트 성공'}
          {status === 'test_failed' && '❌ 테스트 실패'}
          {status === 'send_success' && '✅ 발송 완료'}
          {status === 'send_failed' && '❌ 발송 실패'}
          
          {result && (
            <div className="ResultDetail">
              {result.papers_count && <p>논문 수: {result.papers_count}개</p>}
              {result.recipients_count && <p>수신자: {result.recipients_count}명</p>}
              {result.pdf_size && <p>PDF 크기: {Math.round(result.pdf_size / 1024)}KB</p>}
              {result.error && <p className="ErrorText">오류: {result.error}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MailingSendPanel;