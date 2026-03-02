```typescript
'use client';

import React, { useState } from 'react';
import { useInsiderActivity } from '@/hooks/useInsiderActivity';
import { ChevronLeftIcon, ChevronRightIcon, ExternalLinkIcon } from '@heroicons/react/outline';

export function InsiderFilings() {
  const {
    filings,
    meta,
    loading,
    error,
    filters,
    setTicker,
    setTransactionType,
    setMinDays,
    setOffset,
  } = useInsiderActivity();

  const getTransactionColor = (type: string) => {
    switch (type) {
      case 'purchase':
        return 'bg-green-50 text-green-900';
      case 'sale':
        return 'bg-red-50 text-red-900';
      case 'grant':
        return 'bg-blue-50 text-blue-900';
      case 'exercise':
        return 'bg-purple-50 text-purple-900';
      default:
        return 'bg-slate-50 text-slate-900';
    }
  };

  const getSentimentIcon = (score: number) => {
    if (score > 0.5) return '📈';
    if (score < -0.5) return '📉';
    return '↔️';
  };

  if (loading && filings.length === 0) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-slate-200 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      {/* Filters */}
      <div className="p-4 border-b border-slate-200 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            type="text"
            placeholder="Filter by ticker..."
            value={filters.ticker || ''}
            onChange={(e) => setTicker(e.target.value || null)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <select
            value={filters.transactionType || 'all'}
            onChange={(e) => setTransactionType(e.target.value === 'all' ? null : e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="purchase">Purchases</option>
            <option value="sale">Sales</option>
            <option value="grant">Grants</option>
            <option value="exercise">Exercises</option>
          </select>

          <select
            value={filters.minDays}
            onChange={(e) => setMinDays(parseInt(e.target.value))}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200 text-red-900 text-sm">{error}</div>
      )}

      {filings.length === 0 && !loading && (
        <div className="p-8 text-center text-slate-500">No insider filings found</div>
      )}

      {filings.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-slate-900">Insider</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-slate-900">Type</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-slate-900">Shares</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-slate-900">Price</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-slate-900">Sentiment</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-slate-900">Date</th>
                </tr>
              </thead>
              <tbody>
                {filings.map((filing) => (
                  <tr key={filing.id} className="border-b border-slate-200 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-slate-900">{filing.insider_name}</div>
                      <div className="text-xs text-slate-600">{filing.title}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getTransactionColor(filing.transaction_type)}`}>
                        {filing.transaction_type.charAt(0).toUpperCase() + filing.transaction_type.slice(1)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-slate-900">
                      {filing.shares.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-slate-900">
                      ${filing.price.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-lg">{getSentimentIcon(filing.sentiment_score)}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      <a
                        href={filing.filing_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
                      >
                        {new Date(filing.filing_date).toLocaleDateString()}
                        <ExternalLinkIcon className="w-3 h-3" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between text-sm">
            <div className="text-slate-600">
              Showing {meta.offset + 1} to {Math.min(meta.offset + meta.limit, meta.total_count)} of{' '}
              {meta.total_count}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, meta.offset - meta.limit))}
                disabled={meta.offset === 0}
                className="p-2 hover:bg-slate-100 rounded disabled:opacity-50"
              >
                <ChevronLeftIcon className="w-5 h-5" />
              </button>
              <button
                onClick={() => setOffset(meta.offset + meta.limit)}
                disabled={!meta.has_next}
                className="p-2 hover:bg-slate-100 rounded disabled:opacity-50"
              >
                <ChevronRightIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
```