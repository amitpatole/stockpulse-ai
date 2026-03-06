```typescript
'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, Plus, Loader2, X, Settings } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import {
  getRatings,
  addStock,
  deleteStock,
  searchStocks,
  getWatchlistGroups,
  reorderGroupStocks,
} from '@/lib/api';
import type { AIRating, StockSearchResult, WatchlistGroup } from '@/lib/types';
import StockCard from './StockCard';
import WatchlistGroupsModal from './WatchlistGroups';
import { useDragDrop } from '@/hooks/useDragDrop';

export default function StockGrid() {
  const { data: ratings, loading, error, refetch } = useApi<AIRating[]>(getRatings, [], {
    refreshInterval: 30000,
  });

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [highlightIdx, setHighlightIdx] = useState(-1);
  const [groups, setGroups] = useState<WatchlistGroup[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [showGroupsModal, setShowGroupsModal] = useState(false);
  const [groupsLoading, setGroupsLoading] = useState(false);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Load groups on mount
  useEffect(() => {
    loadGroups();
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadGroups = async () => {
    try {
      const data = await getWatchlistGroups();
      setGroups(data);
    } catch (err) {
      console.error('Failed to load groups:', err);
    }
  };

  const handleGroupsChange = () => {
    loadGroups();
    refetch();
  };

  // Filter ratings by selected group
  const filteredRatings = selectedGroupId
    ? ratings?.filter(r => {
        // This would need group info in the rating object
        // For now, show all when a group is selected
        return true;
      })
    : ratings;

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    setSearching(true);
    try {
      const data = await searchStocks(q);
      setResults(data);
      setShowDropdown(data.length > 0);
      setHighlightIdx(-1);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);
    setAddError(null);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 300);
  };

  const handleSelect = async (result: StockSearchResult) => {
    setShowDropdown(false);
    setQuery('');
    setResults([]);
    setAdding(true);
    setAddError(null);
    try {
      await addStock(result.ticker, result.name);
      refetch();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : 'Failed to add stock');
    } finally {
      setAdding(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || results.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIdx((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIdx((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter' && highlightIdx >= 0) {
      e.preventDefault();
      handleSelect(results[highlightIdx]);
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  };

  async function handleRemoveStock(tickerToRemove: string) {
    try {
      await deleteStock(tickerToRemove);
      refetch();
    } catch {
      // Silently handle for now
    }
  }

  return (
    <div>
      {/* Search & Add Stock Bar */}
      <div ref={wrapperRef} className="relative mb-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleInputChange(e.target.value)}
              onFocus={() => { if (results.length > 0) setShowDropdown(true); }}
              onKeyDown={handleKeyDown}
              placeholder="Search stocks (e.g., AAPL, Tesla, Reliance)..."
              className="w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2.5 pl-10 pr-10 text-sm text-white placeholder-slate-500 outline-none transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50"
              maxLength={40}
            />
            {(searching || adding) && (
              <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-slate-400" />
            )}
            {!searching && !adding && query && (
              <button
                onClick={() => { setQuery(''); setResults([]); setShowDropdown(false); setAddError(null); }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <button
            onClick={() => setShowGroupsModal(true)}
            className="rounded-lg border border-slate-700 bg-slate-800/50 p-2.5 text-slate-400 hover:text-white transition-colors"
            title="Manage watchlist groups"
          >
            <Settings className="h-4 w-4" />
          </button>
        </div>

        {/* Search Results Dropdown */}
        {showDropdown && (
          <div className="absolute z-50 mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 shadow-xl">
            {results.map((result, idx) => (
              <button
                key={result.ticker}
                onClick={() => handleSelect(result)}
                className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm transition-colors first:rounded-t-lg last:rounded-b-lg ${
                  idx === highlightIdx
                    ? 'bg-blue-600/20 text-white'
                    : 'text-slate-300 hover:bg-slate-700/50'
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{result.ticker}</span>
                    <span className="rounded bg-slate-700/50 px-1.5 py-0.5 text-xs text-slate-400">
                      {result.exchange}
                    </span>
                    {result.type === 'ETF' && (
                      <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-xs text-amber-400">
                        ETF
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 truncate text-xs text-slate-400">{result.name}</p>
                </div>
                <Plus className="ml-3 h-4 w-4 flex-shrink-0 text-slate-500" />
              </button>
            ))}
          </div>
        )}
      </div>

      {addError && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {addError}
        </div>
      )}

      {/* Group Tabs */}
      {groups.length > 0 && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedGroupId(null)}
            className={`flex-shrink-0 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              selectedGroupId === null
                ? 'bg-blue-600 text-white'
                : 'border border-slate-700 text-slate-300 hover:bg-slate-800/50'
            }`}
          >
            All
          </button>
          {groups.map((group) => (
            <button
              key={group.id}
              onClick={() => setSelectedGroupId(group.id)}
              className={`flex-shrink-0 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                selectedGroupId === group.id
                  ? 'text-white'
                  : 'border border-slate-700 text-slate-300 hover:bg-slate-800/50'
              }`}
              style={{
                backgroundColor: selectedGroupId === group.id ? group.color : 'transparent',
                borderColor: group.color,
              }}
            >
              {group.name} ({group.stock_count})
            </button>
          ))}
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
              <p className="mt-1 text-xs text-slate-500">Search for a stock above to get started.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {filteredRatings?.map((rating) => (
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

      {/* Watchlist Groups Modal */}
      <WatchlistGroupsModal
        isOpen={showGroupsModal}
        onClose={() => setShowGroupsModal(false)}
        onGroupsChange={handleGroupsChange}
      />
    </div>
  );
}
```