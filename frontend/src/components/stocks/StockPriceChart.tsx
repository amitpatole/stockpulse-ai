'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useApi } from '@/hooks/useApi';
import { getStockDetail, getComparisonData } from '@/lib/api';
import type { Timeframe, StockDetail, ComparisonResult, ComparisonSeries } from '@/lib/types';
import PriceChart from '@/components/charts/PriceChart';
import TimeframeToggle from './TimeframeToggle';
import ComparisonChart from './ComparisonChart';
import ComparisonModePanel from './ComparisonModePanel';

const STORAGE_KEY = 'vo_chart_timeframe';
const VALID_TIMEFRAMES: Timeframe[] = ['1D', '1W', '1M', '3M', '1Y', 'All'];

function getInitialTimeframe(): Timeframe {
  if (typeof window === 'undefined') return '1M';
  const stored = localStorage.getItem(STORAGE_KEY);
  return VALID_TIMEFRAMES.includes(stored as Timeframe) ? (stored as Timeframe) : '1M';
}

interface ComparisonTicker {
  ticker: string;
  name: string;
  error: string | null;
}

function parseCompareParam(param: string): ComparisonTicker[] {
  return param
    .split(',')
    .map((t) => t.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, 4)
    .map((t) => ({ ticker: t, name: t, error: null }));
}

interface StockPriceChartProps {
  ticker: string;
  initialCompare?: string;
}

export default function StockPriceChart({ ticker, initialCompare = '' }: StockPriceChartProps) {
  const router = useRouter();
  const [timeframe, setTimeframe] = useState<Timeframe>(getInitialTimeframe);
  const [comparisonEnabled, setComparisonEnabled] = useState<boolean>(
    () => initialCompare.trim().length > 0
  );
  const [comparisonTickers, setComparisonTickers] = useState<ComparisonTicker[]>(
    () => (initialCompare.trim() ? parseCompareParam(initialCompare) : [])
  );
  const [comparisonData, setComparisonData] = useState<ComparisonResult | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  // Skip URL sync on first mount — the URL already reflects initialCompare
  const isMounted = useRef(false);

  // Sync comparison state → ?compare= URL param (skip initial mount)
  useEffect(() => {
    if (!isMounted.current) {
      isMounted.current = true;
      return;
    }
    const params = new URLSearchParams(window.location.search);
    if (comparisonEnabled && comparisonTickers.length > 0) {
      params.set('compare', comparisonTickers.map((c) => c.ticker).join(','));
    } else {
      params.delete('compare');
    }
    const qs = params.toString();
    router.replace(qs ? `?${qs}` : window.location.pathname, { scroll: false });
  }, [comparisonEnabled, comparisonTickers, router]);

  const fetcher = useCallback(
    () => getStockDetail(ticker, timeframe),
    [ticker, timeframe]
  );

  const { data, loading, error } = useApi<StockDetail>(fetcher, [ticker, timeframe]);

  const chartData =
    data?.candles.map((c) => ({ time: c.time, value: c.close })) ?? [];

  // Refresh comparison data whenever tickers, timeframe, or mode changes
  useEffect(() => {
    if (!comparisonEnabled) {
      setComparisonData(null);
      setComparisonError(null);
      return;
    }

    const allTickers = [ticker, ...comparisonTickers.map((c) => c.ticker)];

    let cancelled = false;
    setComparisonLoading(true);
    setComparisonError(null);

    getComparisonData(allTickers, timeframe)
      .then((result) => {
        if (cancelled) return;
        // Propagate per-ticker errors back to pills
        setComparisonTickers((prev) =>
          prev.map((ct) => {
            const found = result.series.find((s) => s.ticker === ct.ticker);
            return { ...ct, error: found?.error ?? null };
          })
        );
        setComparisonData(result);
      })
      .catch((err) => {
        if (cancelled) return;
        setComparisonError(err instanceof Error ? err.message : 'Failed to load comparison data');
      })
      .finally(() => {
        if (!cancelled) setComparisonLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [comparisonEnabled, ticker, comparisonTickers, timeframe]);

  function handleTimeframeChange(tf: Timeframe) {
    localStorage.setItem(STORAGE_KEY, tf);
    setTimeframe(tf);
  }

  function handleToggleComparison(enabled: boolean) {
    setComparisonEnabled(enabled);
    if (!enabled) {
      setComparisonTickers([]);
      setComparisonData(null);
    }
  }

  function handleAddTicker(ct: ComparisonTicker) {
    setComparisonTickers((prev) => {
      if (prev.find((p) => p.ticker === ct.ticker)) return prev;
      return [...prev, ct];
    });
  }

  function handleRemoveTicker(tickerToRemove: string) {
    setComparisonTickers((prev) => prev.filter((p) => p.ticker !== tickerToRemove));
  }

  // Build series array for ComparisonChart; inject errors from state
  const comparisonSeries: ComparisonSeries[] = comparisonData
    ? comparisonData.series.map((s) => {
        const local = comparisonTickers.find((c) => c.ticker === s.ticker);
        return { ...s, error: local?.error ?? s.error };
      })
    : [];

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900 p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-white">Price History</h2>
        <TimeframeToggle selected={timeframe} onChange={handleTimeframeChange} />
      </div>

      {/* Comparison mode panel (toggle + search + pills) */}
      <ComparisonModePanel
        primaryTicker={ticker}
        comparisonTickers={comparisonTickers}
        onAdd={handleAddTicker}
        onRemove={handleRemoveTicker}
        onToggle={handleToggleComparison}
        enabled={comparisonEnabled}
      />

      {/* Loading state */}
      {(loading || (comparisonEnabled && comparisonLoading)) && (
        <div className="flex items-center justify-center py-20">
          <Loader2
            className="h-6 w-6 animate-spin text-slate-400"
            aria-hidden="true"
          />
          <span className="sr-only">Loading chart data…</span>
        </div>
      )}

      {/* Error state */}
      {!loading && !comparisonLoading && (error || (comparisonEnabled && comparisonError)) && (
        <div
          className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400"
          role="alert"
        >
          {comparisonEnabled && comparisonError ? comparisonError : error}
        </div>
      )}

      {/* Standard single-ticker chart */}
      {!comparisonEnabled && !loading && !error && chartData.length === 0 && (
        <p className="py-12 text-center text-sm text-slate-500">
          No data available for this period
        </p>
      )}

      {!comparisonEnabled && !loading && !error && chartData.length > 0 && (
        <div className="mt-4">
          <PriceChart data={chartData} height={320} timeframe={timeframe} />
        </div>
      )}

      {/* Comparison chart */}
      {comparisonEnabled && !comparisonLoading && !comparisonError && comparisonSeries.length > 0 && (
        <div className="mt-4 rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <ComparisonChart
            series={comparisonSeries}
            height={320}
            timeframe={timeframe}
          />
        </div>
      )}

      {/* Comparison mode — waiting for at least one comparison ticker */}
      {comparisonEnabled && !comparisonLoading && !comparisonError && comparisonTickers.length === 0 && (
        <p className="mt-6 py-8 text-center text-sm text-slate-500">
          Search for a ticker above to start comparing
        </p>
      )}
    </div>
  );
}
