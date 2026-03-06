```javascript
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { RateLimitCard } from '../components/RateLimitCard';

const Dashboard = () => {
  const [rateLimits, setRateLimits] = useState([]);
  const router = useRouter();

  useEffect(() => {
    fetch(`/api/rate_limit`)
      .then(response => response.json())
      .then(data => setRateLimits(data));
  }, []);

  return (
    <div>
      <h1>API Rate Limit Dashboard</h1>
      {rateLimits.map(rl => (
        <RateLimitCard key={rl.id} rateLimit={rl} />
      ))}
    </div>
  );
};

export default Dashboard;
```