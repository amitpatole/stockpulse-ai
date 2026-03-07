```typescript
import React from 'react';

interface CryptoPriceCardProps {
  ticker: string;
  price: number;
}

const CryptoPriceCard: React.FC<CryptoPriceCardProps> = ({ ticker, price }) => {
  return (
    <div className="bg-slate-800 p-4 rounded-lg shadow-lg">
      <h2 className="text-xl font-semibold text-slate-200">{ticker}</h2>
      <p className="mt-2 text-lg font-medium text-slate-400">Current Price: ${price.toFixed(2)}</p>
    </div>
  );
};

export default CryptoPriceCard;
```