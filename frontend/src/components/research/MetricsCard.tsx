```typescript
'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';
import type { ResearchBriefMetrics } from '@/lib/types';

interface MetricsCardProps {
  metrics?: ResearchBriefMetrics;
}

export default function MetricsCard({ metrics }: MetricsCardProps) {
  if (!metrics) {
    return null;
  }

  const formatValue = (value: unknown, type: string): string => {
    if (value === null || value === undefined) return '—';
    if (type === 'rsi') return `${Number(value).toFixed(1)}`;
    if (type === 'sentiment') return `${Number(value).toFixed(1)}/100`;
    if (type === 'price') return `${Number(value):+.2f}%`;
    if (type === 'level') return `$${Number(value).toFixed(2)}`;
    return String(value).toUpperCase();
  };

  const renderMetricItem = (label: string, value: unknown, type: string) => {
    const displayValue = formatValue(value, type);
    if (displayValue === '—') return null;

    const isPrice = type === 'price';
    const numValue = typeof value === 'number' ? value : 0;
    const isBullish = numValue > 0;

    return (
      <div key={label} className="rounded-lg border border-slate-700/30 bg-slate-800/20 p-3">
        <div className="text-xs font-medium text-slate-500 mb-1">{label}</div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">{displayValue}</span>
          {isPrice && numValue !== 0 && (
            <div className={`flex items-center gap-0.5 text-xs ${isBullish ? 'text-green-400' : 'text-red-400'}`}>
              {isBullish ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="mb-6">
      <h3 className="mb-3 text-sm font-semibold text-slate-200">Key Metrics</h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {renderMetricItem('RSI', metrics.rsi, 'rsi')}
        {renderMetricItem('MACD Signal', metrics.macd_signal, 'signal')}
        {renderMetricItem('Sentiment', metrics.sentiment_score, 'sentiment')}
        {renderMetricItem('Price Change (24h)', metrics.price_change_pct, 'price')}
        {renderMetricItem('Support Level', metrics.support_level, 'level')}
        {renderMetricItem('Resistance Level', metrics.resistance_level, 'level')}
      </div>
    </div>
  );
}
```