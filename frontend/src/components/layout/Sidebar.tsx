```typescript
import React from 'react';
import { Link } from 'react-router-dom';
import CryptoGrid from './CryptoGrid';

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-slate-800 text-slate-200 p-4">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">Dashboard</h2>
        <p className="mt-1 text-slate-400">Market overview and monitoring</p>
      </div>
      <CryptoGrid tickers={['BTC', 'ETH', 'LTC']} />
    </aside>
  );
};

export default Sidebar;
```