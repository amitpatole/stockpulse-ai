```typescript
'use client';

import React, { useState, useCallback } from 'react';
import { format } from 'date-fns';
import { ChevronDown } from 'lucide-react';
import { useEconomicCalendar } from '@/hooks/useEconomicCalendar';

const COUNTRIES = ['US', 'EU', 'UK', 'JP', 'AU', 'CA'];
const CATEGORIES = [
  'employment',
  'inflation',
  'gdp',
  'interest_rates',
  'housing',
  'consumer',
];

export const CalendarView: React.FC = () => {
  const [filters, setFilters] = useState({
    country: '',
    category: '',
    minImpact: '',
  });

  const { events, loading, error, hasMore, loadMore } = useEconomicCalendar({
    country: filters.country || undefined,
    category: filters.category || undefined,
    minImpact: filters.minImpact || undefined,
  });

  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Country
            </label>
            <select
              value={filters.country}
              onChange={(e) => handleFilterChange('country', e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Countries</option>
              {COUNTRIES.map((country) => (
                <option key={country} value={country}>
                  {country}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={filters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Impact
            </label>
            <select
              value={filters.minImpact}
              onChange={(e) => handleFilterChange('minImpact', e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Levels</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {error && (
          <div className="bg-red-50 border-b border-red-200 p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="divide-y divide-gray-200">
          {loading && events.length === 0 ? (
            <div className="p-8 text-center text-gray-500">Loading events...</div>
          ) : events.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No events found</div>
          ) : (
            events.map((event) => (
              <div key={event.id} className="p-4 hover:bg-gray-50 transition">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{event.event_name}</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {event.country} • {event.category.replace('_', ' ')}
                    </p>
                    <p className="text-sm text-gray-600 mt-2">
                      Scheduled: {format(new Date(event.scheduled_datetime), 'MMM d, yyyy h:mm a')}
                    </p>
                    {event.forecast_value && (
                      <p className="text-sm text-gray-600">
                        Forecast: <span className="font-medium">{event.forecast_value}</span>
                        {event.previous_value && ` (Prev: ${event.previous_value})`}
                      </p>
                    )}
                  </div>

                  <span className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ml-4 ${
                    event.impact_level === 'high'
                      ? 'bg-red-100 text-red-800'
                      : event.impact_level === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {event.impact_level.toUpperCase()}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {hasMore && (
          <div className="border-t border-gray-200 p-4 text-center">
            <button
              onClick={loadMore}
              disabled={loading}
              className="text-blue-600 hover:text-blue-700 disabled:text-gray-400 font-medium"
            >
              {loading ? 'Loading...' : 'Load More'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
```