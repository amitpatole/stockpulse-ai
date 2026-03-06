'use client';

import React, { useEffect, useState } from 'react';
import { EarningsRecord } from '@/types/earnings';
import { formatEarningsDate } from '@/lib/api/earnings';

interface EarningsDetailProps {
  earning: EarningsRecord | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EarningsDetail: React.FC<EarningsDetailProps> = ({
  earning,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !earning) return null;

  const surprise =
    earning.actual_eps !== null && earning.estimated_eps !== null
      ? ((earning.actual_eps - earning.estimated_eps) / earning.estimated_eps) * 100
      : null;

  const getSurpriseColor = (value: number | null) => {
    if (value === null) return 'text-gray-600';
    if (value > 0.5) return 'text-green-600';
    if (value < -0.5) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{earning.ticker}</h2>
              <p className="text-sm text-gray-600 mt-1">
                {formatEarningsDate(earning.earnings_date)}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Details */}
          <div className="space-y-4 mb-6">
            {/* EPS Section */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">EPS</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Estimated</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {earning.estimated_eps !== null ? earning.estimated_eps.toFixed(2) : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Actual</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {earning.actual_eps !== null ? earning.actual_eps.toFixed(2) : '—'}
                  </p>
                </div>
              </div>
              {surprise !== null && (
                <div className={`mt-2 text-sm font-semibold ${getSurpriseColor(surprise)}`}>
                  {surprise > 0 ? '+' : ''}{surprise.toFixed(1)}% Surprise
                </div>
              )}
            </div>

            {/* Revenue Section */}
            {(earning.estimated_revenue || earning.actual_revenue) && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Revenue (B)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Estimated</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {earning.estimated_revenue !== null
                        ? `$${earning.estimated_revenue.toFixed(1)}`
                        : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Actual</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {earning.actual_revenue !== null
                        ? `$${earning.actual_revenue.toFixed(1)}`
                        : '—'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Fiscal Info */}
            {(earning.fiscal_quarter || earning.fiscal_year) && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Fiscal Period</h3>
                <p className="text-sm text-gray-700">
                  {earning.fiscal_quarter} {earning.fiscal_year}
                </p>
              </div>
            )}
          </div>

          {/* Status Badge */}
          <div className="flex items-center justify-between pt-4 border-t">
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                earning.status === 'upcoming'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {earning.status === 'upcoming' ? 'Upcoming' : 'Reported'}
            </span>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md text-sm font-medium hover:bg-gray-300"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
};