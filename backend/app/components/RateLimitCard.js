```javascript
import React from 'react';

const RateLimitCard = ({ rateLimit }) => {
  return (
    <div className="rate-limit-card">
      <h2>{rateLimit.provider.name}</h2>
      <p>Usage: {rateLimit.usage}</p>
      <p>Limit: {rateLimit.limit}</p>
      <p>Quota: {rateLimit.quota}</p>
    </div>
  );
};

export default RateLimitCard;
```