```typescript
'use client';

import React, { useMemo } from 'react';
import { useInsiderStats } from '@/hooks/useInsiderStats';

interface InsiderStatsProps {
  cik: string;
  ticker?: string;
}

export function InsiderStats({ cik, ticker }: InsiderStatsProps) {
  const { stats, loading, error, period, setPeriod } = useInsiderStats(cik);

  const buyRatio = useMemo(() => {
    if (!stats) return 0;
    const total = stats.buy_count + stats.sell_count;
    return total > 0 ? ((stats.buy_count / total) * 100).toFixed(1) : 0;
  }, [stats]);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-slate-200 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return <div className="text-red-600 text-sm">{error || 'Failed to load stats'}</div>;
  }

  const getSentimentColor = (avg: number) => {
    if (avg > 0.5) return 'text-green-600';
    if (avg < -0.5) return 'text-red-600';
    return 'text-yellow-600';
  };

  return (
    <div className="space-y-4">
      {/* Period selector */}
      <div className="flex gap-2">
        {([7, 30, 90] as const).map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              period === p
                ? 'bg-blue-600 text-white'
                : 'bg-slate-200 text-slate-900 hover:bg-slate-300'
            }`}
          >
            {p}d
          </button>
        ))}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <p className="text-xs font-medium text-slate-600 mb-1">Net Shares</p>
          <p className="text-2xl font-bold text-slate-900">{stats.net_shares.toLocaleString()}</p>
          <p className="text-xs text-slate-600 mt-1">({stats.period_days}d)</p>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <p className="text-xs font-medium text-slate-600 mb-1">Sentiment</p>
          <p className={`text-2xl font-bold ${getSentimentColor(stats.sentiment_avg)}`}>
            {stats.sentiment_avg > 0 ? '+' : ''}{stats.sentiment_avg.toFixed(2)}
          </p>
          <p className="text-xs text-slate-600 mt-1">Average</p>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <p className="text-xs font-medium text-slate-600 mb-1">Buy/Sell Ratio</p>
          <p className="text-2xl font-bold text-slate-900">{buyRatio}%</p>
          <p className="text-xs text-slate-600 mt-1">
            {stats.buy_count}/{stats.sell_count}
          </p>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <p className="text-xs font-medium text-slate-600 mb-1">Insiders</p>
          <p className="text-2xl font-bold text-slate-900">{stats.insider_count}</p>
          <p className="text-xs text-slate-600 mt-1">Active</p>
        </div>
      </div>

      {/* Value summary */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <p className="text-sm font-medium text-slate-900 mb-3">Transaction Values</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-slate-600">Total Buys</p>
            <p className="text-lg font-bold text-green-600">
              ${(stats.total_buy_value / 1_000_000).toFixed(1)}M
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-600">Total Sells</p>
            <p className="text-lg font-bold text-red-600">
              ${(stats.total_sell_value / 1_000_000).toFixed(1)}M
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```