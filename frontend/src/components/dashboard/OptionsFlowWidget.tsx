```typescript
/**
 * TickerPulse AI - Options Flow Widget
 * Real-time dashboard widget showing unusual options activity and alerts.
 */

import React, { useState } from 'react';
import { AlertBadge } from '@/components/options/AlertBadge';
import { FlowTable } from '@/components/options/FlowTable';
import { useOptionsFlowData } from '@/hooks/useOptionsFlow';

export function OptionsFlowWidget() {
  const { flows, isLoading, error } = useOptionsFlowData({ limit: 10 });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedFlowType, setSelectedFlowType] = useState<string>();
  const [minScore, setMinScore] = useState(0);

  const filteredFlows = flows.filter(f => {
    if (selectedFlowType && f.flow_type !== selectedFlowType) return false;
    if (f.anomaly_score < minScore) return false;
    return true;
  });

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="relative">
            <h2 className="text-xl font-bold text-slate-100">Options Flow Monitor</h2>
            <AlertBadge />
          </div>
          <span className="text-xs text-slate-400">Real-time activity tracking</span>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="px-3 py-1 bg-slate-800 text-slate-300 rounded text-sm hover:bg-slate-700 transition-colors"
        >
          Filters
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="mb-6 pb-6 border-b border-slate-700 space-y-4">
          <div>
            <label className="text-sm text-slate-300 block mb-2">Flow Type</label>
            <select
              value={selectedFlowType || ''}
              onChange={e => setSelectedFlowType(e.target.value || undefined)}
              className="w-full bg-slate-800 text-slate-200 rounded px-3 py-2 text-sm border border-slate-600 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="unusual_volume">Unusual Volume</option>
              <option value="large_trade">Large Trade</option>
              <option value="put_call_imbalance">Put/Call Imbalance</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-300 block mb-2">
              Min Anomaly Score: {minScore}
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={minScore}
              onChange={e => setMinScore(Number(e.target.value))}
              className="w-full"
            />
          </div>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="text-center py-8 text-slate-400">Loading...</div>
      ) : error ? (
        <div className="text-center py-8 text-red-400">{error}</div>
      ) : filteredFlows.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          No options flows match your filters
        </div>
      ) : (
        <FlowTable />
      )}

      {/* Footer */}
      <div className="mt-6 pt-6 border-t border-slate-700">
        <p className="text-xs text-slate-400">
          Updated every 60 seconds during market hours. {flows.length} total flows recorded.
        </p>
      </div>
    </div>
  );
}
```