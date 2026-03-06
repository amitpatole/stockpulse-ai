```typescript
'use client';

import React, { useMemo } from 'react';
import { EarningsDisplayRecord } from '@/types/earnings';
import { getEPSStatus, formatEarningsDate } from '@/lib/api/earnings';

interface EarningsTableProps {
  earnings: EarningsDisplayRecord[];
  isLoading?: boolean;
  onEarningClick?: (earning: EarningsDisplayRecord) => void;
}

export const EarningsTable: React.FC<EarningsTableProps> = ({
  earnings,
  isLoading = false,
  onEarningClick,
}) => {
  const enrichedEarnings = useMemo(() => {
    const today = new Date();
    return earnings.map((e) => {
      const epsStatus = e.actual_eps !== null ? getEPSStatus(e.surprise_percent) : null;
      return {
        ...e,
        epsStatus,
      };
    });
  }, [earnings]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'beat':
        return 'text-green-600 bg-green-50';
      case 'miss':
        return 'text-red-600 bg-red-50';
      case 'neutral':
        return 'text-gray-600 bg-gray-50';
      default:
        return '';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center text-gray-500">Loading earnings...</div>
      </div>
    );
  }

  if (earnings.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center text-gray-500">
          No earnings found. Add stocks to your watchlist to see earnings data.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Ticker
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Date
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
              Est. EPS
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
              Act. EPS
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
              Surprise
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {enrichedEarnings.map((earning) => (
            <tr
              key={earning.id}
              onClick={() => onEarningClick?.(earning)}
              className="hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="font-semibold text-blue-600">{earning.ticker}</span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                {formatEarningsDate(earning.earnings_date)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                {earning.estimated_eps !== null ? earning.estimated_eps.toFixed(2) : '—'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                {earning.actual_eps !== null ? earning.actual_eps.toFixed(2) : '—'}
              </td>
              <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${getStatusColor(earning.epsStatus || '')}`}>
                {earning.surprise_percent !== null
                  ? `${earning.surprise_percent > 0 ? '+' : ''}${earning.surprise_percent.toFixed(1)}%`
                  : earning.status === 'upcoming'
                    ? 'Pending'
                    : '—'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  earning.status === 'upcoming'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {earning.status === 'upcoming' ? 'Upcoming' : 'Reported'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```