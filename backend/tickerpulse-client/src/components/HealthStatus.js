```javascript
import React from 'react';

const HealthStatus = ({ healthStatus }) => {
  const { status, timestamp, latency, error_rate } = healthStatus;

  return (
    <div>
      <h3>Status: {status}</h3>
      <p>Timestamp: {timestamp}</p>
      <p>Latency: {latency}</p>
      <p>Error Rate: {error_rate}</p>
    </div>
  );
};

export default HealthStatus;
```