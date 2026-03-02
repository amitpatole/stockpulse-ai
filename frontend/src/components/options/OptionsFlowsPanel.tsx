/**
 * TickerPulse AI - Options Flows Panel Component
 * Displays real-time options flow activity with filtering and sorting.
 */

import React, { useState, useMemo } from 'react';
import { useOptionsFlows } from '@/hooks/useOptionsFlows';
import type { OptionsFlow } from '@/hooks/useOptionsFlows';

interface OptionsFlowsPanelProps {
  ticker?: string;
  limit?: number;
}

type SortField = 'ticker' | 'unusual_ratio' | 'volume' | 'detected_at';
type SortOrder = 'asc' | 'desc';

export function OptionsFlowsPanel({ ticker, limit = 50 }: OptionsFlowsPanelProps) {
  const { flows, isLoading, error } = useOptionsFlows({
    ticker,
    minRatio: 2.0,
    pollIntervalMs: 5000,
  });

  const [sortField, setSortField] = useState<SortField>('detected_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [filterType, setFilterType] = useState<string>('all');

  const filteredFlows = useMemo(() => {
    let filtered = flows;

    if (filterType !== 'all') {
      filtered = filtered.filter((f) => f.flow_type === filterType);
    }

    return filtered.slice(0, limit);
  }, [flows, filterType, limit]);

  const sortedFlows = useMemo(() => {
    const sorted = [...filteredFlows];
    sorted.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }

      return 0;
    });
    return sorted;
  }, [filteredFlows, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const getFlowTypeColor = (type: string) => {
    switch (type) {
      case 'call_spike':
        return 'bg-green-500/20 text-green-400';
      case 'put_spike':
        return 'bg-red-500/20 text-red-400';
      case 'unusual_volume':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-slate-500/20 text-slate-400';
    }
  };

  const getRatioBadgeColor = (ratio: number) => {
    if (ratio >= 5.0) return 'bg-red-500/20 text-red-400';
    if (ratio >= 3.0) return 'bg-orange-500/20 text-orange-400';
    return 'bg-yellow-500/20 text-yellow-400';
  };

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/50 p-4">
        <p className="text-sm text-red-200">Error loading flows: {error}</p>
      </div>
    );
  }

  if (isLoading && sortedFlows.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-slate-400">Loading options flows...</div>
      </div>
    );
  }

  if (sortedFlows.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-8 text-center">
        <p className="text-slate-400">No options flows detected</p>
        <p className="text-xs text-slate-500 mt-2">
          Unusual activity will appear here when detected
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            filterType === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilterType('call_spike')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            filterType === 'call_spike'
              ? 'bg-green-600 text-white'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Calls
        </button>
        <button
          onClick={() => setFilterType('put_spike')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            filterType === 'put_spike'
              ? 'bg-red-600 text-white'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Puts
        </button>
        <button
          onClick={() => setFilterType('unusual_volume')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            filterType === 'unusual_volume'
              ? 'bg-yellow-600 text-white'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Volume
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 sticky top-0">
            <tr>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('ticker')}
              >
                Ticker {sortField === 'ticker' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-200">Type</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-200">Strike</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-200">Expiry</th>
              <th
                className="px-4 py-3 text-right font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('volume')}
              >
                Volume {sortField === 'volume' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="px-4 py-3 text-right font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('unusual_ratio')}
              >
                Ratio {sortField === 'unusual_ratio' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-200">Action</th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('detected_at')}
              >
                Detected {sortField === 'detected_at' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {sortedFlows.map((flow) => (
              <tr key={flow.id} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3 font-semibold text-slate-200">{flow.ticker}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      flow.option_type === 'call'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {flow.option_type.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300 font-mono text-xs">
                  ${flow.strike_price.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-slate-300 text-xs">{flow.expiry_date}</td>
                <td className="px-4 py-3 text-right text-slate-300">
                  {flow.volume.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getRatioBadgeColor(flow.unusual_ratio)}`}>
                    {flow.unusual_ratio.toFixed(1)}x
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getFlowTypeColor(flow.flow_type)}`}>
                    {flow.flow_type.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">
                  {new Date(flow.detected_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}