'use client';

import { useEffect, useState, useCallback } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { getProviderRateLimits } from '@/lib/api';
import type { ProviderRateLimit, ProviderRateLimitsResponse } from '@/lib/types';

const STATUS_BAR_CLASS: Record<string, string> = {
  ok:       'bg-emerald-500',
  warning:  'bg-amber-400',
  critical: 'bg-red-500',
  unknown:  'bg-slate-600',
};

const STATUS_TEXT_CLASS: Record<string, string> = {
  ok:       'text-emerald-400',
  warning:  'text-amber-400',
  critical: 'text-red-400',
  unknown:  'text-slate-400',
};

const STATUS_BADGE_CLASS: Record<string, string> = {
  ok:       'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  warning:  'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  critical: 'bg-red-500/20 text-red-400 border border-red-500/30',
  unknown:  'bg-slate-700/50 text-slate-400 border border-slate-600/30',
};

function useCountdown(resetAt: string | null): string {
  const [display, setDisplay] = useState('');

  useEffect(() => {
    if (!resetAt) {
      setDisplay('');
      return;
    }

    function tick() {
      const secs = Math.max(0, Math.round((new Date(resetAt!).getTime() - Date.now()) / 1000));
      setDisplay(secs > 0 ? `${secs}s` : 'now');
    }

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [resetAt]);

  return display;
}

function ProviderRow({ provider }: { provider: ProviderRateLimit }) {
  const countdown = useCountdown(provider.reset_at);
  const barPct = Math.min(provider.pct_used, 100);

  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-slate-800/70 last:border-0">
      {/* Provider name */}
      <div className="w-28 flex-shrink-0">
        <span className="text-xs font-medium text-slate-300 truncate block">{provider.display_name}</span>
      </div>

      {/* Progress bar + usage label */}
      <div className="flex-1 min-w-0">
        {provider.status === 'unknown' ? (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 rounded-full bg-slate-800" />
            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${STATUS_BADGE_CLASS.unknown}`}>
              Limit unknown
            </span>
          </div>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${STATUS_BAR_CLASS[provider.status]}`}
                  style={{ width: `${barPct}%` }}
                />
              </div>
              <span className={`text-xs font-medium tabular-nums ${STATUS_TEXT_CLASS[provider.status]}`}>
                {provider.requests_used} / {provider.requests_limit} req/min
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Reset countdown */}
      <div className="w-12 text-right flex-shrink-0">
        {countdown ? (
          <span className="text-xs text-slate-500 tabular-nums">
            {countdown}
          </span>
        ) : (
          <span className="text-xs text-slate-600">—</span>
        )}
      </div>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-slate-800/70 last:border-0 animate-pulse">
      <div className="w-28 h-3 rounded bg-slate-800 flex-shrink-0" />
      <div className="flex-1 h-1.5 rounded-full bg-slate-800" />
      <div className="w-12 h-3 rounded bg-slate-800 flex-shrink-0" />
    </div>
  );
}

export default function ProviderRateLimitPanel() {
  const [data, setData] = useState<ProviderRateLimitsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await getProviderRateLimits();
      setData(result);
      setError(null);
    } catch {
      setError('Provider status unavailable');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, [load]);

  return (
    <div className="rounded-xl bg-slate-900 border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-blue-400" />
          <span className="text-sm font-semibold text-white">API Rate Limits</span>
        </div>
        <button
          onClick={load}
          className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="px-4 py-2">
        {/* Column headers */}
        <div className="flex items-center gap-3 pb-1">
          <div className="w-28 flex-shrink-0">
            <span className="text-xs text-slate-500">Provider</span>
          </div>
          <div className="flex-1">
            <span className="text-xs text-slate-500">Usage (last 60s)</span>
          </div>
          <div className="w-12 text-right flex-shrink-0">
            <span className="text-xs text-slate-500">Reset</span>
          </div>
        </div>

        {loading && !data && (
          <>
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </>
        )}

        {error && !loading && (
          <div className="py-6 text-center text-sm text-slate-500">
            {error}
          </div>
        )}

        {!error && data && data.providers.length === 0 && (
          <div className="py-6 text-center text-sm text-slate-500">
            No data providers configured
          </div>
        )}

        {!error && data && data.providers.map(p => (
          <ProviderRow key={p.name} provider={p} />
        ))}
      </div>
    </div>
  );
}
