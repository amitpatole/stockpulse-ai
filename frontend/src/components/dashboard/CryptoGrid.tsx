```typescript
import React from 'react';
import CryptoPriceCard from './CryptoPriceCard';

interface CryptoGridProps {
  tickers: string[];
}

const CryptoGrid: React.FC<CryptoGridProps> = ({ tickers }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {tickers.map(ticker => (
        <CryptoPriceCard key={ticker} ticker={ticker} price={100} /> {/* Replace with actual price fetching */}
      ))}
    </div>
  );
};

export default CryptoGrid;
```