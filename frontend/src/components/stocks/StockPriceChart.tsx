'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { getStockDetail, getCompareData } from '@/lib/api';
import type { Timeframe, StockDetail, CompareResponse } from '@/lib/types';
import PriceChart from '@/components/charts/PriceChart';
import TimeframeToggle from './TimeframeToggle';
import CompareInput from './CompareInput';

const STORAGE_KEY = 'vo_chart_timeframe';
const VALID_TIMEFRAMES: Timeframe[] = ['1D', '1W', '1M', '3M', '1Y', 'All'];
const COMPARISON_PALETTE = ['#f59e0b', '#10b981', '#8b5cf6', '#ef4444'];

function getInitialTimeframe(): Timeframe {
  if (typeof window === 'undefined') return '1M';
  const stored = localStorage.getItem(STORAGE_KEY);
  return VALID_TIMEFRAMES.includes(stored as Timeframe) ? (stored as Timeframe) : '1M';
}

function parseCompareParam(): string[] {
  if (typeof window === 'undefined') return [];
  const params = new URLSearchParams(window.location.search);
  const raw = params.get('compare');
  if (!raw) return [];
  return raw
    .split(',')
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, 4);
}

interface CompareOverlay {
  symbol: string;
  color: string;
  points: { time: number; value: number }[];
  current_pct: number;
}

interface StockPriceChartProps {
  ticker: string;
}

export default function StockPriceChart({ ticker }: StockPriceChartProps) {
  const router = useRouter();

  const [timeframe, setTimeframe] = useState<Timeframe>(getInitialTimeframe);
  const [compareSymbols, setCompareSymbols] = useState<string[]>(parseCompareParam);
  const [compareData, setCompareData] = useState<CompareResponse | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const isFirstMount = useRef(true);

  const fetcher = useCallback(
    () => getStockDetail(ticker, timeframe),
    [ticker, timeframe]
  );
  const { data, loading, error } = useApi<StockDetail>(fetcher, [ticker, timeframe]);

  // Sync compareSymbols → URL (skip first mount to avoid spurious navigation)
  useEffect(() => {
    if (isFirstMount.current) {
      isFirstMount.current = false;
      return;
    }
    const params = new URLSearchParams(window.location.search);
    if (compareSymbols.length > 0) {
      params.set('compare', compareSymbols.join(','));
    } else {
      params.delete('compare');
    }
    const qs = params.toString();
    router.replace(`${window.location.pathname}${qs ? `?${qs}` : ''}`);
  }, [compareSymbols, router]);

  // Fetch comparison data when symbols or timeframe changes
  useEffect(() => {
    if (compareSymbols.length === 0 || timeframe === 'All') {
      setCompareData(null);
      return;
    }

    let cancelled = false;
    setCompareLoading(true);

    getCompareData(compareSymbols, timeframe)
      .then((result) => {
        if (!cancelled) setCompareData(result);
      })
      .catch(() => {
        if (!cancelled) setCompareData(null);
      })
      .finally(() => {
        if (!cancelled) setCompareLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [compareSymbols, timeframe]);

  function handleTimeframeChange(tf: Timeframe) {
    localStorage.setItem(STORAGE_KEY, tf);
    setTimeframe(tf);
  }

  function handleAddSymbol(symbol: string) {
    if (symbol === ticker || compareSymbols.includes(symbol)) return;
    if (compareSymbols.length >= 4) return;
    setCompareSymbols((prev) => [...prev, symbol]);
  }

  function handleRemoveSymbol(symbol: string) {
    setCompareSymbols((prev) => prev.filter((s) => s !== symbol));
  }

  const isComparing = compareSymbols.length > 0 && timeframe !== 'All';

  // Build overlays for PriceChart
  const compareOverlays: CompareOverlay[] = compareSymbols
    .map((symbol, idx) => {
      if (!compareData) return null;
      const entry = compareData[symbol];
      if (!entry || 'error' in entry) return null;
      return {
        symbol,
        color: COMPARISON_PALETTE[idx % COMPARISON_PALETTE.length],
        points: entry.points,
        current_pct: entry.current_pct,
      };
    })
    .filter((o): o is CompareOverlay => o !== null);

  // Normalize primary candles to % return when comparing
  const chartData = (() => {
    if (!data?.candles?.length) return [];
    if (!isComparing) {
      return data.candles.map((c) => ({ time: c.time, value: c.close }));
    }
    const firstClose = data.candles[0].close;
    if (!firstClose) return data.candles.map((c) => ({ time: c.time, value: c.close }));
    return data.candles.map((c) => ({
      time: c.time,
      value: Math.round(((c.close / firstClose - 1) * 100 + Number.EPSILON) * 10000) / 10000,
    }));
  })();

  // Collect per-symbol error warnings
  const warnings: Record<string, string> = {};
  if (compareData) {
    for (const symbol of compareSymbols) {
      const entry = compareData[symbol];
      if (entry && 'error' in entry) {
        warnings[symbol] = entry.error;
      }
    }
  }

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900 p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-white">Price History</h2>
        <TimeframeToggle selected={timeframe} onChange={handleTimeframeChange} />
      </div>

      {/* Comparison input — chips + text field */}
      <CompareInput
        symbols={compareSymbols}
        colors={COMPARISON_PALETTE}
        warnings={warnings}
        onAdd={handleAddSymbol}
        onRemove={handleRemoveSymbol}
        loading={compareLoading}
      />

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2
            className="h-6 w-6 animate-spin text-slate-400"
            aria-hidden="true"
          />
          <span className="sr-only">Loading chart data…</span>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div
          className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* No data */}
      {!loading && !error && chartData.length === 0 && (
        <p className="py-12 text-center text-sm text-slate-500">
          No data available for this period
        </p>
      )}

      {/* Chart — single or comparison mode */}
      {!loading && !error && chartData.length > 0 && (
        <div className="mt-4">
          <PriceChart
            data={chartData}
            height={320}
            timeframe={timeframe}
            primarySymbol={isComparing ? ticker : undefined}
            compareOverlays={isComparing ? compareOverlays : undefined}
          />
        </div>
      )}
    </div>
  );
}
