import React, { useState, useEffect } from 'react';
import { mailingAPI } from '../utils/api';

const MailingConfig = () => {
  const [config, setConfig] = useState({
    smtpHost: '',
    smtpPort: 587,
    smtpUser: '',
    smtpPassword: '',
    fromEmail: '',
    fromName: 'arXiv Newsletter',
    testEmail: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [testResult, setTestResult] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      console.log('DEBUG: Loading config...');
      const response = await mailingAPI.getConfig();
      console.log('DEBUG: Load response:', response.data);
      
      if (response.data.success && response.data.config) {
        console.log('DEBUG: Setting config:', response.data.config);
        // 비밀번호는 유지 (서버에서 빈 문자열로 옴)
        setConfig(prev => ({
          ...response.data.config,
          smtpPassword: prev.smtpPassword || response.data.config.smtpPassword
        }));
      } else {
        console.log('DEBUG: No config found, using defaults');
      }
    } catch (err) {
      console.error('ERROR loading config:', err);
      console.error('ERROR Details:', err.response);
    }
  };

  const saveConfig = async () => {
    if (!config.smtpHost || !config.smtpUser || !config.fromEmail) {
      setError('SMTP 호스트, 사용자명, 발신자 이메일은 필수입니다.');
      return;
    }

    console.log('DEBUG: Saving config:', config);
    setLoading(true);
    try {
      const response = await mailingAPI.saveConfig(config);
      console.log('DEBUG: Save response:', response.data);
      
      if (response.data.success) {
        alert('설정이 저장되었습니다.');
        setError('');
        // 저장 후 다시 로드
        await loadConfig();
      } else {
        setError(response.data.error || '설정 저장 실패');
      }
    } catch (err) {
      setError('설정 저장 실패: ' + err.message);
      console.error('ERROR:', err);
      console.error('ERROR Details:', err.response);
    } finally {
      setLoading(false);
    }
  };

  const testConfig = async () => {
    if (!config.testEmail) {
      setError('테스트 이메일 주소를 입력하세요.');
      return;
    }

    if (!config.smtpPassword) {
      setError('비밀번호를 입력하세요.');
      return;
    }

    console.log('DEBUG: Testing with config:', {
      ...config,
      smtpPassword: '***'
    });

    setLoading(true);
    setTestResult('');
    try {
      const response = await mailingAPI.testConfig({
        ...config,
        testEmail: config.testEmail
      });
      
      console.log('DEBUG: Test response:', response.data);
      
      if (response.data.success) {
        setTestResult('테스트 이메일이 성공적으로 전송되었습니다.');
        setError('');
      } else {
        setError(response.data.error || '테스트 실패');
      }
    } catch (err) {
      setError('테스트 실패: ' + err.message);
      console.error('ERROR:', err);
      console.error('ERROR Details:', err.response);
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
          {testResult && (
            <div style={{backgroundColor: '#ecfdf5', color: 'var(--success)', border: '1px solid #d1fae5', padding: '1rem', borderRadius: 'var(--radius)', marginBottom: '1.5rem'}}>
              {testResult}
            </div>
          )}
          
          <div style={{backgroundColor: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd', padding: '1rem', borderRadius: 'var(--radius)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
            <i className="fas fa-info-circle"></i>
            <div>
              <strong>SMTP 설정 필요</strong>
              <p>이메일 전송 기능을 활성화하려면 SMTP 서버 정보를 설정하세요.</p>
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
                    value={config.smtpHost}
                    onChange={(e) => setConfig({...config, smtpHost: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">SMTP 포트</label>
                  <input
                    type="number"
                    className="FormControl"
                    placeholder="587"
                    value={config.smtpPort}
                    onChange={(e) => setConfig({...config, smtpPort: parseInt(e.target.value)})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">사용자명</label>
                  <input
                    type="email"
                    className="FormControl"
                    placeholder="your-email@gmail.com"
                    value={config.smtpUser}
                    onChange={(e) => setConfig({...config, smtpUser: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">비밀번호</label>
                  <input
                    type="password"
                    className="FormControl"
                    placeholder="앱 비밀번호"
                    value={config.smtpPassword}
                    onChange={(e) => setConfig({...config, smtpPassword: e.target.value})}
                  />
                </div>
                
                <button className="Button Button--success" onClick={saveConfig} disabled={loading}>
                  <i className="fas fa-save"></i> SMTP 설정 저장
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
                    value={config.fromEmail}
                    onChange={(e) => setConfig({...config, fromEmail: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">발신자 이름</label>
                  <input
                    type="text"
                    className="FormControl"
                    placeholder="arXiv Newsletter"
                    value={config.fromName}
                    onChange={(e) => setConfig({...config, fromName: e.target.value})}
                  />
                </div>
                
                <div className="FormGroup">
                  <label className="FormLabel">테스트 이메일</label>
                  <input
                    type="email"
                    className="FormControl"
                    placeholder="test@example.com"
                    value={config.testEmail}
                    onChange={(e) => setConfig({...config, testEmail: e.target.value})}
                  />
                </div>
                
                <div style={{display: 'flex', gap: '1rem'}}>
                  <button className="Button Button--primary" onClick={saveConfig} disabled={loading}>
                    <i className="fas fa-save"></i> 발신자 정보 저장
                  </button>
                  <button className="Button Button--warning" onClick={testConfig} disabled={loading || !config.testEmail}>
                    <i className="fas fa-paper-plane"></i> {loading ? '테스트 중...' : '테스트 발송'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="Card">
        <div className="CardHeader">
          <h2 className="CardTitle">설정 가이드</h2>
        </div>
        <div className="CardBody">
          <div className="Grid">
            <div style={{padding: '1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius)'}}>
              <h4 style={{marginBottom: '0.5rem', color: 'var(--primary)'}}>Gmail 설정</h4>
              <p style={{fontSize: '0.875rem', color: 'var(--text-light)', marginBottom: '0.5rem'}}>
                호스트: smtp.gmail.com<br/>
                포트: 587<br/>
                보안: STARTTLS
              </p>
              <p style={{fontSize: '0.875rem', color: 'var(--warning)'}}>
                Gmail의 경우 앱 비밀번호를 사용하세요.
              </p>
              <p style={{fontSize: '0.75rem', color: 'var(--text-light)', marginTop: '0.5rem'}}>
                1. Google 계정 설정 → 보안<br/>
                2. 2단계 인증 활성화<br/>
                3. 앱 비밀번호 생성<br/>
                4. 생성된 16자리 비밀번호 사용
              </p>
            </div>
            
            <div style={{padding: '1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius)'}}>
              <h4 style={{marginBottom: '0.5rem', color: 'var(--primary)'}}>Outlook 설정</h4>
              <p style={{fontSize: '0.875rem', color: 'var(--text-light)', marginBottom: '0.5rem'}}>
                호스트: smtp-mail.outlook.com<br/>
                포트: 587<br/>
                보안: STARTTLS
              </p>
            </div>
            
            <div style={{padding: '1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius)'}}>
              <h4 style={{marginBottom: '0.5rem', color: 'var(--primary)'}}>보안 팁</h4>
              <p style={{fontSize: '0.875rem', color: 'var(--text-light)'}}>
                • 2단계 인증 활성화<br/>
                • 앱 전용 비밀번호 사용<br/>
                • 정기적인 비밀번호 변경
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MailingConfig;
