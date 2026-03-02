```typescript
'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useInsiderActivity } from '@/hooks/useInsiderActivity';

export function InsiderActivityWidget() {
  const { filings, loading, error } = useInsiderActivity();
  const [sentimentColor, setSentimentColor] = useState('text-slate-600');

  useEffect(() => {
    if (filings.length === 0) {
      setSentimentColor('text-slate-400');
      return;
    }

    const avgSentiment = filings.reduce((sum, f) => sum + f.sentiment_score, 0) / filings.length;

    if (avgSentiment > 0.5) {
      setSentimentColor('text-green-600');
    } else if (avgSentiment < -0.5) {
      setSentimentColor('text-red-600');
    } else {
      setSentimentColor('text-yellow-600');
    }
  }, [filings]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 border border-slate-200">
        <div className="h-16 bg-slate-100 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <Link href="/dashboard/insiders">
      <div className="bg-white rounded-lg shadow-sm p-4 border border-slate-200 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-600">Insider Activity</p>
            <p className={`text-2xl font-bold ${sentimentColor}`}>
              {filings.length > 0 ? `${filings.length} filings` : 'No activity'}
            </p>
            <p className="text-xs text-slate-500 mt-1">(Last 7 days)</p>
          </div>
          <div className={`text-4xl ${sentimentColor} opacity-20`}>📊</div>
        </div>
        {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
      </div>
    </Link>
  );
}
```