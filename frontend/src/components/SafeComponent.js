import React, { useState } from 'react';

function SafeComponent({ children, fallback = null, componentName = 'Component' }) {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    console.error('ERROR:', JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'ERROR',
      message: `${componentName} render failed`,
      trace: `SafeComponent:${componentName}`
    }));
    
    return fallback || (
      <div className="SafeComponentError">
        <h3>ERROR</h3>
        <p>{componentName} failed to load</p>
        <button onClick={() => setHasError(false)}>Retry</button>
      </div>
    );
  }

  try {
    return children;
  } catch (error) {
    console.error('ERROR:', JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'ERROR',
      message: error.message,
      trace: error.stack
    }));
    setHasError(true);
    return null;
  }
}

export default SafeComponent;
