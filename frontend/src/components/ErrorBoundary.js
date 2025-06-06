import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ERROR:', JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'ERROR',
      message: error.message,
      trace: error.stack
    }));
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="ErrorFallback">
          <h2>ERROR</h2>
          <p>Check console for details</p>
          <button onClick={() => window.location.reload()}>Reload</button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
