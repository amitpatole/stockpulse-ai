'use client';

import { TrendingUp, TrendingDown, Minus, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { AIRating } from '@/lib/types';
import { RATING_BG_CLASSES } from '@/lib/types';

interface StockCardProps {
  rating: AIRating;
  onRemove?: (ticker: string) => void;
}

export default function StockCard({ rating, onRemove }: StockCardProps) {
  const priceChangePct = rating.price_change_pct ?? 0;
  const isPositive = priceChangePct > 0;
  const isNegative = priceChangePct < 0;

  const ratingClass = RATING_BG_CLASSES[rating.rating] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';

  const sentimentScore = rating.sentiment_score ?? 0;
  const sentimentPct = Math.round(((sentimentScore + 1) / 2) * 100); // -1 to 1 -> 0% to 100%

  return (
    <div className="group relative rounded-xl border border-slate-700/50 bg-slate-800/50 p-4 transition-all hover:border-slate-600 hover:bg-slate-800">
      {/* Remove button */}
      {onRemove && (
        <button
          onClick={() => onRemove(rating.ticker)}
          className="absolute right-2 top-2 rounded p-1 text-slate-600 opacity-0 transition-opacity hover:bg-slate-700 hover:text-slate-300 group-hover:opacity-100"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}

      {/* Header: Ticker + Price */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-base font-bold text-white">{rating.ticker}</h3>
          <p className="mt-0.5 text-xl font-bold text-white font-mono">
            ${rating.current_price?.toFixed(2) ?? '—'}
          </p>
        </div>
        <div
          className={clsx(
            'flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium',
            isPositive && 'bg-emerald-500/10 text-emerald-400',
            isNegative && 'bg-red-500/10 text-red-400',
            !isPositive && !isNegative && 'bg-slate-500/10 text-slate-400'
          )}
        >
          {isPositive ? (
            <TrendingUp className="h-3 w-3" />
          ) : isNegative ? (
            <TrendingDown className="h-3 w-3" />
          ) : (
            <Minus className="h-3 w-3" />
          )}
          <span className="font-mono">
            {isPositive ? '+' : ''}{priceChangePct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* AI Rating Badge */}
      <div className="mt-3">
        <span
          className={clsx(
            'inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold',
            ratingClass
          )}
        >
          {rating.rating?.replace('_', ' ') ?? 'N/A'}
          {rating.confidence != null && (
            <span className="ml-1.5 opacity-70">
              {Math.round(rating.confidence * 100)}%
            </span>
          )}
        </span>
      </div>

      {/* Metrics Row */}
      <div className="mt-3 grid grid-cols-2 gap-3">
        {/* RSI */}
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500">RSI</p>
          <div className="mt-1 flex items-center gap-2">
            <span
              className={clsx(
                'text-sm font-bold font-mono',
                rating.rsi > 70 ? 'text-red-400' : rating.rsi < 30 ? 'text-emerald-400' : 'text-slate-300'
              )}
            >
              {rating.rsi?.toFixed(1) ?? '—'}
            </span>
            <div className="h-1.5 flex-1 rounded-full bg-slate-700">
              <div
                className={clsx(
                  'h-full rounded-full',
                  rating.rsi > 70 ? 'bg-red-500' : rating.rsi < 30 ? 'bg-emerald-500' : 'bg-blue-500'
                )}
                style={{ width: `${Math.min(100, (rating.rsi ?? 0))}%` }}
              />
            </div>
          </div>
        </div>

        {/* Sentiment */}
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500">Sentiment</p>
          <div className="mt-1 flex items-center gap-2">
            <span
              className={clsx(
                'text-sm font-bold font-mono',
                sentimentScore > 0.2 ? 'text-emerald-400' : sentimentScore < -0.2 ? 'text-red-400' : 'text-slate-300'
              )}
            >
              {sentimentScore > 0 ? '+' : ''}{sentimentScore.toFixed(2)}
            </span>
            <div className="h-1.5 flex-1 rounded-full bg-slate-700">
              <div
                className={clsx(
                  'h-full rounded-full',
                  sentimentScore > 0.2 ? 'bg-emerald-500' : sentimentScore < -0.2 ? 'bg-red-500' : 'bg-amber-500'
                )}
                style={{ width: `${sentimentPct}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Score */}
      {rating.score != null && (
        <div className="mt-3 flex items-center justify-between border-t border-slate-700/50 pt-3">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">AI Score</span>
          <span className="text-sm font-bold font-mono text-white">{rating.score.toFixed(1)}/10</span>
        </div>
      )}
    </div>
  );
}
