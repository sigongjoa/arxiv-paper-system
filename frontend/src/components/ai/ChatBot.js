import React, { useState, useRef, useEffect } from 'react';
import './ChatBot.css';

const ChatBot = ({ paperData, isOpen, onClose, sessionId = 'default' }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatMode, setChatMode] = useState('chat');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && paperData) {
      setMessages([{
        type: 'assistant',
        content: `안녕하세요! "${paperData.title}"에 대해 질문해보세요.`,
        timestamp: new Date().toISOString(),
        confidence: 100
      }]);
    }
  }, [isOpen, paperData]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_id: paperData.arxiv_id,
          message: inputValue,
          session_id: sessionId
        })
      });

      const data = await response.json();
      
      const assistantMessage = {
        type: 'assistant',
        content: data.answer || data.error || '응답을 생성할 수 없습니다.',
        timestamp: new Date().toISOString(),
        confidence: data.confidence || 0,
        sources: data.sources || [],
        error: !!data.error
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: '죄송합니다. 오류가 발생했습니다.',
        timestamp: new Date().toISOString(),
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = async () => {
    try {
      await fetch(`/api/ai/chat/clear/${sessionId}`, { method: 'DELETE' });
      setMessages([{
        type: 'assistant',
        content: `대화가 초기화되었습니다. "${paperData.title}"에 대해 다시 질문해보세요.`,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Clear chat error:', error);
    }
  };

  const runAnalysis = async (analysisType) => {
    setIsLoading(true);
    setChatMode('analysis');
    
    try {
      let endpoint = '';
      switch (analysisType) {
        case 'comprehensive':
          endpoint = '/api/ai/analyze/comprehensive';
          break;
        case 'findings':
          endpoint = '/api/ai/extract/findings';
          break;
        case 'quality':
          endpoint = '/api/ai/assess/quality';
          break;
        case 'questions':
          endpoint = '/api/ai/generate/questions';
          break;
        default:
          return;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ arxiv_id: paperData.arxiv_id })
      });

      const data = await response.json();
      
      const analysisMessage = {
        type: 'analysis',
        analysisType,
        content: data,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, analysisMessage]);
    } catch (error) {
      console.error('Analysis error:', error);
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: '분석 중 오류가 발생했습니다.',
        timestamp: new Date().toISOString(),
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="chatbot-overlay">
      <div className="chatbot-container">
        <div className="chatbot-header">
          <div className="chatbot-title">
            <div className="title-text">Research Assistant</div>
            <div className="paper-info">
              {paperData?.arxiv_id && (
                <span className="arxiv-badge">{paperData.arxiv_id}</span>
              )}
            </div>
          </div>
          <div className="chatbot-controls">
            <button className="control-btn" onClick={clearChat} title="대화 초기화">
              🗑️
            </button>
            <button className="control-btn close-btn" onClick={onClose} title="닫기">
              ✕
            </button>
          </div>
        </div>

        <div className="chatbot-modes">
          <button 
            className={`mode-btn ${chatMode === 'chat' ? 'active' : ''}`}
            onClick={() => setChatMode('chat')}
          >
            Chat
          </button>
          <button 
            className={`mode-btn ${chatMode === 'analysis' ? 'active' : ''}`}
            onClick={() => setChatMode('analysis')}
          >
            Analysis
          </button>
        </div>

        {chatMode === 'analysis' && (
          <div className="analysis-tools">
            <button className="analysis-btn" onClick={() => runAnalysis('comprehensive')}>
              종합 분석
            </button>
            <button className="analysis-btn" onClick={() => runAnalysis('findings')}>
              핵심 발견
            </button>
            <button className="analysis-btn" onClick={() => runAnalysis('quality')}>
              품질 평가
            </button>
            <button className="analysis-btn" onClick={() => runAnalysis('questions')}>
              연구 질문
            </button>
          </div>
        )}

        <div className="chatbot-messages">
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
          {isLoading && <LoadingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        <div className="chatbot-input">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="논문에 대해 질문해보세요..."
            disabled={isLoading}
            rows="2"
          />
          <button 
            className="send-btn" 
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
      </div>
    </div>
  );
};

const ChatMessage = ({ message }) => {
  const renderContent = () => {
    if (message.type === 'analysis') {
      return <AnalysisResult data={message.content} type={message.analysisType} />;
    }

    return (
      <div className="message-content">
        <p>{message.content}</p>
        {message.confidence !== undefined && (
          <div className="message-metadata">
            <span className="confidence">신뢰도: {message.confidence}%</span>
            {message.sources?.length > 0 && (
              <div className="sources">
                출처: {message.sources.join(', ')}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`message ${message.type} ${message.error ? 'error' : ''}`}>
      <div className="message-avatar">
        {message.type === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-body">
        {renderContent()}
        <div className="message-time">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

const AnalysisResult = ({ data, type }) => {
  const renderAnalysisContent = () => {
    switch (type) {
      case 'comprehensive':
        return (
          <div className="analysis-content">
            <h4>📊 종합 분석</h4>
            {data.executive_summary && (
              <div className="analysis-section">
                <strong>요약:</strong>
                <p>{data.executive_summary}</p>
              </div>
            )}
            {data.contributions && (
              <div className="analysis-section">
                <strong>주요 기여:</strong>
                <ul>
                  {data.contributions.map((contrib, idx) => (
                    <li key={idx}>{contrib}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.quality_score && (
              <div className="analysis-section">
                <strong>품질 점수:</strong>
                <div className="score-grid">
                  <span>전체: {data.quality_score.overall}</span>
                  <span>방법론: {data.quality_score.methodology_rigor}</span>
                  <span>참신성: {data.quality_score.novelty}</span>
                </div>
              </div>
            )}
          </div>
        );

      case 'findings':
        return (
          <div className="analysis-content">
            <h4>🔍 핵심 발견사항</h4>
            {data.main_findings && (
              <div className="analysis-section">
                <strong>주요 발견:</strong>
                <ul>
                  {data.main_findings.map((finding, idx) => (
                    <li key={idx}>{finding}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.novel_insights && (
              <div className="analysis-section">
                <strong>새로운 통찰:</strong>
                <ul>
                  {data.novel_insights.map((insight, idx) => (
                    <li key={idx}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      case 'quality':
        return (
          <div className="analysis-content">
            <h4>⭐ 품질 평가</h4>
            {data.quality_assessment && (
              <div className="analysis-section">
                <div className="quality-scores">
                  <div className="score-item">
                    <span>방법론 엄밀성</span>
                    <span>{data.quality_assessment.methodology_rigor}/100</span>
                  </div>
                  <div className="score-item">
                    <span>참신성</span>
                    <span>{data.quality_assessment.novelty}/100</span>
                  </div>
                  <div className="score-item">
                    <span>명확성</span>
                    <span>{data.quality_assessment.clarity}/100</span>
                  </div>
                  <div className="score-item">
                    <span>재현가능성</span>
                    <span>{data.quality_assessment.reproducibility}/100</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case 'questions':
        return (
          <div className="analysis-content">
            <h4>❓ 연구 질문</h4>
            {data.follow_up_questions && (
              <div className="analysis-section">
                <strong>후속 연구:</strong>
                <ul>
                  {data.follow_up_questions.map((question, idx) => (
                    <li key={idx}>{question}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      default:
        return <div>분석 결과를 표시할 수 없습니다.</div>;
    }
  };

  return (
    <div className="analysis-result">
      {renderAnalysisContent()}
    </div>
  );
};

const LoadingIndicator = () => (
  <div className="message assistant">
    <div className="message-avatar">🤖</div>
    <div className="message-body">
      <div className="loading-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </div>
);

export default ChatBot;
