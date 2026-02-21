'use client';

import { useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { getStockDetail } from '@/lib/api';
import type { Timeframe, StockDetail } from '@/lib/types';
import PriceChart from '@/components/charts/PriceChart';
import TimeframeToggle from './TimeframeToggle';

const STORAGE_KEY = 'vo_chart_timeframe';
const VALID_TIMEFRAMES: Timeframe[] = ['1D', '1W', '1M', '3M', '1Y', 'All'];

function getInitialTimeframe(): Timeframe {
  if (typeof window === 'undefined') return '1M';
  const stored = localStorage.getItem(STORAGE_KEY);
  return VALID_TIMEFRAMES.includes(stored as Timeframe) ? (stored as Timeframe) : '1M';
}

interface StockPriceChartProps {
  ticker: string;
}

export default function StockPriceChart({ ticker }: StockPriceChartProps) {
  const [timeframe, setTimeframe] = useState<Timeframe>(getInitialTimeframe);

  const fetcher = useCallback(
    () => getStockDetail(ticker, timeframe),
    [ticker, timeframe]
  );

  const { data, loading, error } = useApi<StockDetail>(fetcher, [ticker, timeframe]);

  function handleTimeframeChange(tf: Timeframe) {
    localStorage.setItem(STORAGE_KEY, tf);
    setTimeframe(tf);
  }

  const chartData =
    data?.candles.map((c) => ({ time: c.time, value: c.close })) ?? [];

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900 p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-white">Price History</h2>
        <TimeframeToggle selected={timeframe} onChange={handleTimeframeChange} />
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2
            className="h-6 w-6 animate-spin text-slate-400"
            aria-hidden="true"
          />
          <span className="sr-only">Loading chart data…</span>
        </div>
      )}

      {error && !loading && (
        <div
          className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && chartData.length === 0 && (
        <p className="py-12 text-center text-sm text-slate-500">
          No data available for this period
        </p>
      )}

      {!loading && !error && chartData.length > 0 && (
        <PriceChart data={chartData} height={320} />
      )}
    </div>
  );
}
