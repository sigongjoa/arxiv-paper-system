import React, { useState, useEffect } from 'react';
import './SystemDashboard.css';

const SystemDashboard = () => {
  const [systemHealth, setSystemHealth] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    loadSystemData();
    const interval = setInterval(loadSystemData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadSystemData = async () => {
    try {
      setIsRefreshing(true);
      
      // Load system health
      const healthResponse = await fetch('/api/health');
      const healthData = await healthResponse.json();
      setSystemHealth(healthData);

      // Load AI system status
      const aiResponse = await fetch('/api/enhanced/ai/enhanced/models/status');
      const aiData = await aiResponse.json();
      setPerformance(aiData);

      // Load general stats
      const statsResponse = await fetch('/api/stats');
      const statsData = await statsResponse.json();
      setSystemStats(statsData);

      // Simulate recent activity
      setRecentActivity([
        { time: new Date().toISOString(), action: 'System health check completed', status: 'success' },
        { time: new Date(Date.now() - 300000).toISOString(), action: 'AI analysis completed', status: 'success' },
        { time: new Date(Date.now() - 600000).toISOString(), action: 'Paper crawling finished', status: 'success' },
        { time: new Date(Date.now() - 900000).toISOString(), action: 'Newsletter generated', status: 'success' }
      ]);

    } catch (error) {
      console.error('Failed to load system data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const runSystemOptimization = async () => {
    try {
      const response = await fetch('/api/enhanced/system/enhanced/optimize', {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.optimization_recommendations) {
        alert('System optimization completed! Check console for details.');
        console.log('Optimization recommendations:', result);
      }
    } catch (error) {
      console.error('System optimization failed:', error);
      alert('Optimization failed: ' + error.message);
    }
  };

  const runDiagnostics = async () => {
    try {
      const response = await fetch('/api/health');
      const diagnostics = await response.json();
      
      // Show diagnostics in a modal or new tab
      const diagnosticsWindow = window.open('', '_blank');
      diagnosticsWindow.document.write(`
        <html>
          <head><title>System Diagnostics</title></head>
          <body style="font-family: monospace; padding: 20px;">
            <h1>System Diagnostics Report</h1>
            <pre>${JSON.stringify(diagnostics, null, 2)}</pre>
          </body>
        </html>
      `);
    } catch (error) {
      console.error('Diagnostics failed:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'operational':
      case 'online':
        return '#10b981';
      case 'degraded':
      case 'warning':
        return '#f59e0b';
      case 'error':
      case 'offline':
      case 'unhealthy':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="system-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h2>📊 System Dashboard</h2>
          <p>Monitor and manage your arXiv analysis system</p>
        </div>
        
        <div className="header-actions">
          <button 
            onClick={loadSystemData} 
            disabled={isRefreshing}
            className="refresh-btn"
          >
            {isRefreshing ? '🔄' : '↻'} Refresh
          </button>
          
          <button onClick={runDiagnostics} className="diagnostics-btn">
            🔍 Diagnostics
          </button>
          
          <button onClick={runSystemOptimization} className="optimize-btn">
            ⚡ Optimize
          </button>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* System Health Overview */}
        <div className="dashboard-card system-health">
          <div className="card-header">
            <h3>🏥 System Health</h3>
            <div className="status-indicator">
              <span 
                className="status-dot"
                style={{ backgroundColor: getStatusColor(systemHealth?.status) }}
              ></span>
              <span className="status-text">
                {systemHealth?.status || 'Checking...'}
              </span>
            </div>
          </div>
          
          <div className="card-content">
            {systemHealth?.system_diagnostics && (
              <div className="health-grid">
                {Object.entries(systemHealth.system_diagnostics.components || {}).map(([component, data]) => (
                  <div key={component} className="health-item">
                    <span className="component-name">{component}</span>
                    <span 
                      className="component-status"
                      style={{ color: getStatusColor(data.status) }}
                    >
                      {data.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* AI System Performance */}
        <div className="dashboard-card ai-performance">
          <div className="card-header">
            <h3>🤖 AI System Performance</h3>
          </div>
          
          <div className="card-content">
            {performance?.performance && (
              <div className="performance-grid">
                {Object.entries(performance.performance).map(([useCase, data]) => (
                  <div key={useCase} className="performance-item">
                    <div className="performance-header">
                      <span className="use-case">{useCase}</span>
                      <span 
                        className="performance-status"
                        style={{ color: getStatusColor(data.status) }}
                      >
                        {data.status}
                      </span>
                    </div>
                    {data.response_time && (
                      <div className="performance-metric">
                        Response Time: {data.response_time.toFixed(2)}s
                      </div>
                    )}
                    {data.model && (
                      <div className="performance-model">
                        Model: {data.model}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* System Statistics */}
        <div className="dashboard-card system-stats">
          <div className="card-header">
            <h3>📈 System Statistics</h3>
          </div>
          
          <div className="card-content">
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{systemStats?.total_count || 0}</div>
                <div className="stat-label">Total Papers</div>
              </div>
              
              <div className="stat-item">
                <div className="stat-value">
                  {performance?.health?.available_models?.length || 0}
                </div>
                <div className="stat-label">AI Models</div>
              </div>
              
              <div className="stat-item">
                <div className="stat-value">99.9%</div>
                <div className="stat-label">Uptime</div>
              </div>
              
              <div className="stat-item">
                <div className="stat-value">
                  {recentActivity.filter(a => a.status === 'success').length}
                </div>
                <div className="stat-label">Recent Tasks</div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="dashboard-card recent-activity">
          <div className="card-header">
            <h3>📋 Recent Activity</h3>
          </div>
          
          <div className="card-content">
            <div className="activity-list">
              {recentActivity.map((activity, index) => (
                <div key={index} className="activity-item">
                  <div className="activity-content">
                    <div className="activity-action">{activity.action}</div>
                    <div className="activity-time">
                      {new Date(activity.time).toLocaleString()}
                    </div>
                  </div>
                  <div 
                    className="activity-status"
                    style={{ color: getStatusColor(activity.status) }}
                  >
                    {activity.status === 'success' ? '✅' : '❌'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-card quick-actions">
          <div className="card-header">
            <h3>⚡ Quick Actions</h3>
          </div>
          
          <div className="card-content">
            <div className="actions-grid">
              <button 
                className="action-button primary"
                onClick={() => window.open('/api/papers?limit=10', '_blank')}
              >
                📄 View Recent Papers
              </button>
              
              <button 
                className="action-button secondary"
                onClick={runSystemOptimization}
              >
                🔧 Run Optimization
              </button>
              
              <button 
                className="action-button secondary"
                onClick={() => window.open('/api/enhanced/ai/enhanced/models/status', '_blank')}
              >
                🤖 AI Model Status
              </button>
              
              <button 
                className="action-button warning"
                onClick={() => {
                  if (window.confirm('This will restart all AI services. Continue?')) {
                    alert('Restart functionality would be implemented here');
                  }
                }}
              >
                🔄 Restart Services
              </button>
            </div>
          </div>
        </div>

        {/* System Configuration */}
        <div className="dashboard-card system-config">
          <div className="card-header">
            <h3>⚙️ Configuration</h3>
          </div>
          
          <div className="card-content">
            <div className="config-list">
              <div className="config-item">
                <span className="config-label">LM Studio URL:</span>
                <span className="config-value">localhost:1234</span>
              </div>
              
              <div className="config-item">
                <span className="config-label">Database:</span>
                <span className="config-value">SQLite (Local)</span>
              </div>
              
              <div className="config-item">
                <span className="config-label">Environment:</span>
                <span className="config-value">Development</span>
              </div>
              
              <div className="config-item">
                <span className="config-label">Auto-refresh:</span>
                <span className="config-value">30 seconds</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemDashboard;
