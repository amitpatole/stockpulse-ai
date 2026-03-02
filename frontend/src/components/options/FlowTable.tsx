```typescript
/**
 * TickerPulse AI - Options Flow Table Component
 * Displays filterable and sortable options flow data.
 */

import React, { useState, useMemo } from 'react';
import { useOptionsFlow } from '@/context/OptionsFlowContext';
import type { OptionFlow } from '@/context/OptionsFlowContext';

interface FlowTableProps {
  ticker?: string;
  flowType?: string;
}

type SortField = 'ticker' | 'anomaly_score' | 'volume' | 'created_at';
type SortOrder = 'asc' | 'desc';

export function FlowTable({ ticker, flowType }: FlowTableProps) {
  const { flows } = useOptionsFlow();
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const filteredFlows = useMemo(() => {
    return flows.filter(f => {
      if (ticker && f.ticker !== ticker) return false;
      if (flowType && f.flow_type !== flowType) return false;
      return true;
    });
  }, [flows, ticker, flowType]);

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

  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-red-500/20 text-red-400';
    if (score >= 60) return 'bg-orange-500/20 text-orange-400';
    return 'bg-yellow-500/20 text-yellow-400';
  };

  const getFlowTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      unusual_volume: 'Unusual Volume',
      large_trade: 'Large Trade',
      put_call_imbalance: 'Put/Call Imbalance',
    };
    return labels[type] || type;
  };

  if (sortedFlows.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        No options flows found. Market may be closed or no unusual activity detected.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-900 sticky top-0">
          <tr>
            <th className="px-4 py-3 text-left font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('ticker')}>
              Ticker {sortField === 'ticker' && (sortOrder === 'asc' ? '↑' : '↓')}
            </th>
            <th className="px-4 py-3 text-left font-semibold text-slate-200">Contract</th>
            <th className="px-4 py-3 text-left font-semibold text-slate-200">Type</th>
            <th className="px-4 py-3 text-right font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('volume')}>
              Volume {sortField === 'volume' && (sortOrder === 'asc' ? '↑' : '↓')}
            </th>
            <th className="px-4 py-3 text-right font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('anomaly_score')}>
              Score {sortField === 'anomaly_score' && (sortOrder === 'asc' ? '↑' : '↓')}
            </th>
            <th className="px-4 py-3 text-left font-semibold text-slate-200">Flow Type</th>
            <th className="px-4 py-3 text-left font-semibold text-slate-200 cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('created_at')}>
              Time {sortField === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700">
          {sortedFlows.map(flow => (
            <tr key={flow.id} className="hover:bg-slate-800/50 transition-colors">
              <td className="px-4 py-3 font-semibold text-slate-200">{flow.ticker}</td>
              <td className="px-4 py-3 text-slate-300 font-mono text-xs">{flow.contract}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  flow.option_type === 'call' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {flow.option_type.toUpperCase()}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-slate-300">{flow.volume.toLocaleString()}</td>
              <td className="px-4 py-3 text-right">
                <span className={`px-2 py-1 rounded text-xs font-semibold ${getScoreBadgeColor(flow.anomaly_score)}`}>
                  {flow.anomaly_score.toFixed(1)}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">
                  {getFlowTypeLabel(flow.flow_type)}
                </span>
              </td>
              <td className="px-4 py-3 text-xs text-slate-400">
                {new Date(flow.created_at).toLocaleTimeString([], {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```