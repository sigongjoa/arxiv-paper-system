import React, { useState, useEffect } from 'react';
import { newsletterAPI } from '../utils/api';
import './NewsletterAutomation.css';

const NewsletterAutomation = () => {
  const [activeSection, setActiveSection] = useState('create');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  
  // Form states
  const [formData, setFormData] = useState({
    recipients: '',
    senderEmail: 'newsletter@example.com',
    domain: 'computer',
    daysBack: 1,
    maxPapers: 10,
    title: 'arXiv Daily Newsletter'
  });

  const [scheduledTasks, setScheduledTasks] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);

  const domains = [
    { value: 'computer', label: 'Computer Science', categories: ['cs.AI', 'cs.LG', 'cs.CL'] },
    { value: 'math', label: 'Mathematics', categories: ['math.CO', 'math.GT', 'math.NT'] },
    { value: 'physics', label: 'Physics', categories: ['physics.comp-ph', 'physics.data-an'] }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateNewsletter = async () => {
    setLoading(true);
    setStatus('creating');
    
    try {
      const recipients = formData.recipients.split(',').map(email => email.trim()).filter(email => email);
      
      // API 호출
      const response = await newsletterAPI.create({
        recipients,
        domain: formData.domain,
        days_back: parseInt(formData.daysBack),
        max_papers: parseInt(formData.maxPapers),
        sender_email: formData.senderEmail,
        title: formData.title
      });
      
      const data = response.data;
      setResult(data);
      setStatus(data.success ? 'success' : 'error');
      
    } catch (error) {
      console.error('Newsletter creation failed:', error);
      setResult({ success: false, error: error.message });
      setStatus('error');
    }
    
    setLoading(false);
  };

  const handleTestGeneration = async () => {
    setLoading(true);
    setStatus('testing');
    
    try {
      const response = await newsletterAPI.test({
        domain: formData.domain,
        max_papers: Math.min(parseInt(formData.maxPapers), 5)
      });
      
      const data = response.data;
      setResult(data);
      setStatus(data.success ? 'success' : 'error');
      
    } catch (error) {
      console.error('Test generation failed:', error);
      setResult({ success: false, error: error.message });
      setStatus('error');
    }
    
    setLoading(false);
  };

  const handleScheduleDaily = async () => {
    setLoading(true);
    
    try {
      const response = await newsletterAPI.schedule({
        recipients: formData.recipients.split(',').map(email => email.trim()),
        domain: formData.domain,
        hour: 9,
        minute: 0
      });
      
      const data = response.data;
      if (data.success) {
        loadScheduledTasks();
      }
      setResult(data);
      
    } catch (error) {
      setResult({ success: false, error: error.message });
    }
    
    setLoading(false);
  };

  const loadScheduledTasks = async () => {
    try {
      const response = await newsletterAPI.getScheduled();
      const data = response.data;
      setScheduledTasks(data.tasks || []);
    } catch (error) {
      console.error('Failed to load scheduled tasks:', error);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const response = await newsletterAPI.getStatus();
      const data = response.data;
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  };

  useEffect(() => {
    if (activeSection === 'schedule') {
      loadScheduledTasks();
    } else if (activeSection === 'status') {
      loadSystemStatus();
    }
  }, [activeSection]);

  return (
    <div className="newsletter-automation">
      {/* Header Section */}
      <div className="automation-header">
        <h1 className="automation-title">Newsletter Automation</h1>
        <p className="automation-tagline">AI-Powered Research Paper Newsletters</p>
        <p className="automation-description">
          Generate and send automated newsletters with the latest arXiv papers, 
          complete with AI summaries and insights.
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="automation-nav">
        <button
          className={`nav-button ${activeSection === 'create' ? 'active' : ''}`}
          onClick={() => setActiveSection('create')}
        >
          <span className="nav-icon">✉️</span>
          Create Newsletter
        </button>
        <button
          className={`nav-button ${activeSection === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveSection('schedule')}
        >
          <span className="nav-icon">📅</span>
          Schedule Daily
        </button>
        <button
          className={`nav-button ${activeSection === 'status' ? 'active' : ''}`}
          onClick={() => setActiveSection('status')}
        >
          <span className="nav-icon">📊</span>
          System Status
        </button>
      </div>

      {/* Main Content */}
      <div className="automation-content">
        
        {/* Create Newsletter Section */}
        {activeSection === 'create' && (
          <div className="content-section">
            <div className="section-header">
              <h2 className="section-title">
                <span className="section-number">1</span>
                Create Newsletter
              </h2>
              <p className="section-subtitle">
                Generate a one-time newsletter with recent papers
              </p>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Recipients</label>
                <textarea
                  name="recipients"
                  value={formData.recipients}
                  onChange={handleInputChange}
                  placeholder="email1@example.com, email2@example.com"
                  className="form-input"
                  rows="3"
                />
                <span className="form-hint">Comma-separated email addresses</span>
              </div>

              <div className="form-group">
                <label className="form-label">Sender Email</label>
                <input
                  type="email"
                  name="senderEmail"
                  value={formData.senderEmail}
                  onChange={handleInputChange}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Research Domain</label>
                <select
                  name="domain"
                  value={formData.domain}
                  onChange={handleInputChange}
                  className="form-input"
                >
                  {domains.map(domain => (
                    <option key={domain.value} value={domain.value}>
                      {domain.label}
                    </option>
                  ))}
                </select>
                <span className="form-hint">
                  Categories: {domains.find(d => d.value === formData.domain)?.categories.join(', ')}
                </span>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Days Back</label>
                  <input
                    type="number"
                    name="daysBack"
                    value={formData.daysBack}
                    onChange={handleInputChange}
                    min="1"
                    max="7"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Max Papers</label>
                  <input
                    type="number"
                    name="maxPapers"
                    value={formData.maxPapers}
                    onChange={handleInputChange}
                    min="1"
                    max="20"
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Newsletter Title</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  className="form-input"
                />
              </div>
            </div>

            <div className="action-buttons">
              <button
                onClick={handleTestGeneration}
                disabled={loading}
                className="action-button secondary"
              >
                {loading && status === 'testing' ? 'Testing...' : 'Test Generation'}
              </button>
              <button
                onClick={handleCreateNewsletter}
                disabled={loading || !formData.recipients.trim()}
                className="action-button primary"
              >
                {loading && status === 'creating' ? 'Creating...' : 'Create & Send Newsletter'}
              </button>
            </div>
          </div>
        )}

        {/* Schedule Section */}
        {activeSection === 'schedule' && (
          <div className="content-section">
            <div className="section-header">
              <h2 className="section-title">
                <span className="section-number">2</span>
                Schedule Daily Newsletter
              </h2>
              <p className="section-subtitle">
                Set up automated daily newsletters
              </p>
            </div>

            <div className="schedule-options">
              <div className="schedule-form">
                <h3>Create New Schedule</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">Recipients</label>
                    <textarea
                      name="recipients"
                      value={formData.recipients}
                      onChange={handleInputChange}
                      placeholder="email1@example.com, email2@example.com"
                      className="form-input"
                      rows="2"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Domain</label>
                    <select
                      name="domain"
                      value={formData.domain}
                      onChange={handleInputChange}
                      className="form-input"
                    >
                      {domains.map(domain => (
                        <option key={domain.value} value={domain.value}>
                          {domain.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <button
                  onClick={handleScheduleDaily}
                  disabled={loading || !formData.recipients.trim()}
                  className="action-button primary"
                >
                  {loading ? 'Scheduling...' : 'Schedule Daily (9:00 AM)'}
                </button>
              </div>

              <div className="scheduled-tasks">
                <h3>Scheduled Tasks</h3>
                {scheduledTasks.length === 0 ? (
                  <div className="empty-state">
                    <p>No scheduled tasks found</p>
                  </div>
                ) : (
                  <div className="tasks-list">
                    {scheduledTasks.map((task, index) => (
                      <div key={index} className="task-item">
                        <div className="task-info">
                          <h4>{task.title}</h4>
                          <p>Recipients: {task.recipients?.length || 0}</p>
                          <p>Domain: {task.domain}</p>
                          <p>Next run: {task.next_run}</p>
                        </div>
                        <div className="task-status">
                          <span className={`status-badge ${task.status}`}>
                            {task.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Status Section */}
        {activeSection === 'status' && (
          <div className="content-section">
            <div className="section-header">
              <h2 className="section-title">
                <span className="section-number">3</span>
                System Status
              </h2>
              <p className="section-subtitle">
                Monitor automation system health
              </p>
            </div>

            {systemStatus && (
              <div className="status-grid">
                <div className="status-card">
                  <div className="status-icon">🤖</div>
                  <h3>LM Studio</h3>
                  <p className="status-value">
                    {systemStatus.llm_status || 'Unknown'}
                  </p>
                </div>

                <div className="status-card">
                  <div className="status-icon">📧</div>
                  <h3>Email Service</h3>
                  <p className="status-value">
                    {systemStatus.email_status || 'Ready'}
                  </p>
                </div>

                <div className="status-card">
                  <div className="status-icon">📄</div>
                  <h3>PDF Generator</h3>
                  <p className="status-value">
                    {systemStatus.pdf_status || 'Ready'}
                  </p>
                </div>

                <div className="status-card">
                  <div className="status-icon">📊</div>
                  <h3>Total Papers</h3>
                  <p className="status-value">
                    {systemStatus.total_papers || '0'}
                  </p>
                </div>
              </div>
            )}

            <button
              onClick={loadSystemStatus}
              className="action-button secondary"
            >
              Refresh Status
            </button>
          </div>
        )}

        {/* Result Display */}
        {result && (
          <div className={`result-section ${status}`}>
            <div className="result-header">
              <h3 className="result-title">
                {status === 'success' ? '✅ Success' : '❌ Error'}
              </h3>
            </div>
            <div className="result-content">
              {result.success ? (
                <div>
                  <p><strong>Papers processed:</strong> {result.papers_count || 'N/A'}</p>
                  {result.pdf_size && (
                    <p><strong>PDF size:</strong> {Math.round(result.pdf_size / 1024)} KB</p>
                  )}
                  {result.emails_sent && (
                    <p><strong>Emails sent:</strong> {result.emails_sent}</p>
                  )}
                  <p><strong>Task ID:</strong> {result.task_id || 'N/A'}</p>
                </div>
              ) : (
                <div>
                  <p><strong>Error:</strong> {result.error || result.message}</p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default NewsletterAutomation;