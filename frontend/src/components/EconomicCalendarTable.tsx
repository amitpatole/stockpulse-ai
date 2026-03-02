import React from 'react';
import { EconomicEventCard } from './EconomicEventCard';
import { EconomicEvent, PaginationMeta } from '@/hooks/useEconomicEvents';

export interface EconomicCalendarTableProps {
  events: EconomicEvent[];
  meta: PaginationMeta;
  loading: boolean;
  error: string | null;
  onFilterChange: {
    startDate: (date: string | null) => void;
    endDate: (date: string | null) => void;
    country: (country: string | null) => void;
    importance: (importance: string | null) => void;
  };
  onPaginate: {
    setLimit: (limit: number) => void;
    setOffset: (offset: number) => void;
  };
}

export function EconomicCalendarTable({
  events,
  meta,
  loading,
  error,
  onFilterChange,
  onPaginate,
}: EconomicCalendarTableProps) {
  const handlePrevious = () => {
    if (meta.offset > 0) {
      onPaginate.setOffset(Math.max(0, meta.offset - meta.limit));
    }
  };

  const handleNext = () => {
    if (meta.has_next) {
      onPaginate.setOffset(meta.offset + meta.limit);
    }
  };

  return (
    <div className="space-y-4">
      {/* Filter Controls */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-4">
        <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex flex-col">
            <label className="text-xs font-medium text-gray-600 mb-1">Start Date</label>
            <input
              type="date"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => onFilterChange.startDate(e.target.value || null)}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs font-medium text-gray-600 mb-1">End Date</label>
            <input
              type="date"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => onFilterChange.endDate(e.target.value || null)}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs font-medium text-gray-600 mb-1">Country</label>
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => onFilterChange.country(e.target.value || null)}
              defaultValue=""
            >
              <option value="">All Countries</option>
              <option value="US">United States</option>
              <option value="EU">European Union</option>
              <option value="UK">United Kingdom</option>
              <option value="JP">Japan</option>
              <option value="CA">Canada</option>
              <option value="AU">Australia</option>
            </select>
          </div>
          <div className="flex flex-col">
            <label className="text-xs font-medium text-gray-600 mb-1">Importance</label>
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => onFilterChange.importance(e.target.value || null)}
              defaultValue=""
            >
              <option value="">All Importance Levels</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200 text-sm">
          <p className="font-semibold">Error loading events</p>
          <p className="text-xs mt-1">{error}</p>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {loading && events.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="mt-2">Loading economic events...</p>
          </div>
        ) : events.length > 0 ? (
          <>
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Event
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Country
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Importance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Scheduled Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Affected Stocks
                  </th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <EconomicEventCard key={event.id} event={event} />
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-xs text-gray-600">
                Showing {meta.offset + 1} to {Math.min(meta.offset + meta.limit, meta.total_count)} of{' '}
                {meta.total_count} events
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handlePrevious}
                  disabled={meta.offset === 0}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={handleNext}
                  disabled={!meta.has_next}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="p-8 text-center text-gray-500">
            <p className="text-sm">No economic events found matching your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}