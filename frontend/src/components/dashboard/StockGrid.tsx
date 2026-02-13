'use client';

import { useState } from 'react';
import { Plus, Loader2 } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { getRatings, addStock, deleteStock } from '@/lib/api';
import type { AIRating } from '@/lib/types';
import StockCard from './StockCard';

export default function StockGrid() {
  const { data: ratings, loading, error, refetch } = useApi<AIRating[]>(getRatings, [], {
    refreshInterval: 30000,
  });
  const [ticker, setTicker] = useState('');
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const handleAddStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) return;

    setAdding(true);
    setAddError(null);
    try {
      await addStock(ticker.trim());
      setTicker('');
      refetch();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : 'Failed to add stock');
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveStock = async (tickerToRemove: string) => {
    try {
      await deleteStock(tickerToRemove);
      refetch();
    } catch {
      // Silently handle for now
    }
  };

  return (
    <div>
      {/* Add Stock Bar */}
      <form onSubmit={handleAddStock} className="mb-4 flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={ticker}
            onChange={(e) => {
              setTicker(e.target.value.toUpperCase());
              setAddError(null);
            }}
            placeholder="Add ticker (e.g., AAPL)"
            className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50"
            maxLength={10}
          />
        </div>
        <button
          type="submit"
          disabled={adding || !ticker.trim()}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {adding ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Plus className="h-4 w-4" />
          )}
          Add
        </button>
      </form>

      {addError && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {addError}
        </div>
      )}

      {/* Loading State */}
      {loading && !ratings && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl border border-slate-700/50 bg-slate-800/30" />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !ratings && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={refetch}
            className="mt-3 rounded-lg bg-slate-700 px-4 py-2 text-sm text-white hover:bg-slate-600 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Stock Cards Grid */}
      {ratings && (
        <>
          {ratings.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-700 bg-slate-800/20 p-12 text-center">
              <p className="text-sm text-slate-400">No stocks monitored yet.</p>
              <p className="mt-1 text-xs text-slate-500">Add a ticker above to get started.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {ratings.map((rating) => (
                <StockCard
                  key={rating.ticker}
                  rating={rating}
                  onRemove={handleRemoveStock}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
