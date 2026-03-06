'use client';

import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import { BriefMetrics, SENTIMENT_COLORS } from '@/lib/types';

interface MetricsDisplayProps {
  metrics?: BriefMetrics;
  ticker?: string;
}

export default function MetricsDisplay({ metrics, ticker }: MetricsDisplayProps) {
  if (!metrics) {
    return (
      <div className="text-sm text-slate-500">
        No metrics available for this brief
      </div>
    );
  }

  const getSentimentBadgeClass = (sentiment?: string): string => {
    if (!sentiment) return 'bg-slate-500/20 text-slate-400';
    const key = sentiment.toLowerCase();
    return SENTIMENT_COLORS[key] || 'bg-slate-500/20 text-slate-400';
  };

  const getRSIStatus = (rsi?: number): { label: string; color: string } => {
    if (!rsi) return { label: 'N/A', color: 'text-slate-400' };
    if (rsi > 70) return { label: 'Overbought', color: 'text-red-400' };
    if (rsi < 30) return { label: 'Oversold', color: 'text-green-400' };
    return { label: 'Neutral', color: 'text-slate-400' };
  };

  const rsiStatus = getRSIStatus(metrics.rsi);

  return (
    <div className="space-y-4">
      {/* Price Section */}
      {(metrics.current_price !== undefined || metrics.price_change_24h_pct !== undefined) && (
        <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-300">Price Action</h3>
          <div className="grid grid-cols-2 gap-4">
            {metrics.current_price !== undefined && (
              <div>
                <p className="text-xs text-slate-500">Current Price</p>
                <p className="mt-1 text-lg font-bold text-white">${metrics.current_price.toFixed(2)}</p>
              </div>
            )}
            {metrics.price_change_24h_pct !== undefined && (
              <div>
                <p className="text-xs text-slate-500">24H Change</p>
                <div className="mt-1 flex items-center gap-1">
                  {metrics.price_change_24h_pct >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-green-400" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-400" />
                  )}
                  <p className={`text-lg font-bold ${
                    metrics.price_change_24h_pct >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {metrics.price_change_24h_pct > 0 ? '+' : ''}{metrics.price_change_24h_pct.toFixed(2)}%
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Technical Indicators */}
      {(metrics.rsi !== undefined || metrics.technical_score !== undefined) && (
        <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-300">Technical Indicators</h3>
          <div className="space-y-3">
            {metrics.rsi !== undefined && (
              <div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-slate-500">RSI (14)</p>
                  <span className={`text-xs font-semibold ${rsiStatus.color}`}>{rsiStatus.label}</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      metrics.rsi > 70 ? 'bg-red-500' : metrics.rsi < 30 ? 'bg-green-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${(metrics.rsi / 100) * 100}%` }}
                  />
                </div>
                <p className="mt-1 text-sm font-medium text-white">{metrics.rsi.toFixed(1)}</p>
              </div>
            )}
            {metrics.technical_score !== undefined && (
              <div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-slate-500">Technical Score</p>
                  <p className="text-xs font-semibold text-blue-400">{(metrics.technical_score * 10).toFixed(1)}/10</p>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-blue-500"
                    style={{ width: `${metrics.technical_score * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sentiment Section */}
      {(metrics.sentiment_label || metrics.sentiment_score !== undefined) && (
        <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-300">Market Sentiment</h3>
          <div className="space-y-2">
            {metrics.sentiment_label && (
              <div>
                <p className="text-xs text-slate-500 mb-2">Sentiment</p>
                <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${getSentimentBadgeClass(metrics.sentiment_label)}`}>
                  {metrics.sentiment_label.charAt(0).toUpperCase() + metrics.sentiment_label.slice(1)}
                </span>
              </div>
            )}
            {metrics.sentiment_score !== undefined && (
              <div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-slate-500">Score</p>
                  <p className="text-xs font-semibold text-emerald-400">{(metrics.sentiment_score * 100).toFixed(1)}%</p>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-500"
                    style={{ width: `${metrics.sentiment_score * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Fundamental Score */}
      {metrics.fundamental_score !== undefined && (
        <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-300">Fundamental Score</p>
            <p className="text-xs font-semibold text-amber-400">{(metrics.fundamental_score * 10).toFixed(1)}/10</p>
          </div>
          <div className="mt-2 h-2 rounded-full bg-slate-700/50 overflow-hidden">
            <div
              className="h-full rounded-full bg-amber-500"
              style={{ width: `${metrics.fundamental_score * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* News Activity */}
      {metrics.news_count_7d !== undefined && (
        <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-slate-500" />
            <div>
              <p className="text-xs text-slate-500">Recent News</p>
              <p className="text-sm font-semibold text-white">{metrics.news_count_7d} articles in last 7 days</p>
            </div>
          </div>
        </div>
      )}

      {/* Data Sources */}
      {metrics.metric_sources && metrics.metric_sources.length > 0 && (
        <div className="text-xs text-slate-500">
          <p className="mb-1">Data from: {metrics.metric_sources.join(', ')}</p>
        </div>
      )}
    </div>
  );
}
