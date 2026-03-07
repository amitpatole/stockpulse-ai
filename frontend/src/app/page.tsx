```typescript
import React from 'react';
import Header from '@/components/layout/Header';
import KPICards from '@/components/dashboard/KPICards';
import StockGrid from '@/components/dashboard/StockGrid';
import CryptoGrid from '@/components/dashboard/CryptoGrid';

export default function DashboardPage() {
  return (
    <div className="flex flex-col">
      <Header title="Dashboard" subtitle="Market overview and monitoring" />
      <main className="flex-1 min-w-0 overflow-x-hidden">
        <KPICards />
        <StockGrid />
        <CryptoGrid tickers={['BTC', 'ETH', 'LTC']} />
      </main>
    </div>
  );
}
```