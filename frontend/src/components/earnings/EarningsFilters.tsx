'use client';

import React, { useState, useCallback } from 'react';
import { EarningsFilterParams } from '@/types/earnings';

interface EarningsFiltersProps {
  onFiltersChange: (params: EarningsFilterParams) => void;
  isLoading?: boolean;
}

export const EarningsFilters: React.FC<EarningsFiltersProps> = ({
  onFiltersChange,
  isLoading = false,
}) => {
  const [status, setStatus] = useState<'upcoming' | 'reported' | ''>('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [ticker, setTicker] = useState('');

  const handleApplyFilters = useCallback(() => {
    const params: EarningsFilterParams = {
      limit: 25,
      offset: 0,
    };

    if (status) params.status = status as 'upcoming' | 'reported';
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (ticker) params.ticker = ticker.toUpperCase();

    onFiltersChange(params);
  }, [status, startDate, endDate, ticker, onFiltersChange]);

  const handleReset = useCallback(() => {
    setStatus('');
    setStartDate('');
    setEndDate('');
    setTicker('');
    onFiltersChange({ limit: 25, offset: 0 });
  }, [onFiltersChange]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as any)}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
          >
            <option value="">All</option>
            <option value="upcoming">Upcoming</option>
            <option value="reported">Reported</option>
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
          />
        </div>

        {/* End Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
          />
        </div>

        {/* Ticker */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Ticker
          </label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="e.g., AAPL"
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleApplyFilters}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400"
        >
          Apply Filters
        </button>
        <button
          onClick={handleReset}
          disabled={isLoading}
          className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md text-sm font-medium hover:bg-gray-300 disabled:bg-gray-100"
        >
          Reset
        </button>
      </div>
    </div>
  );
};