```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';

interface EconomicEvent {
  id: number;
  event_name: string;
  country: string;
  category: string;
  scheduled_datetime: string;
  actual_datetime?: string;
  impact_level: 'low' | 'medium' | 'high';
  forecast_value?: string;
  actual_value?: string;
  previous_value?: string;
  source?: string;
  is_released?: boolean;
}

interface UseEconomicCalendarOptions {
  country?: string;
  category?: string;
  minImpact?: string;
  daysAhead?: number;
  limit?: number;
}

export const useEconomicCalendar = (options: UseEconomicCalendarOptions = {}) => {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const limit = options.limit || 20;

  const fetchEvents = useCallback(
    async (pageOffset: number = 0) => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (options.country) params.append('country', options.country);
        if (options.category) params.append('category', options.category);
        if (options.minImpact) params.append('min_impact', options.minImpact);
        if (options.daysAhead) params.append('days_ahead', options.daysAhead.toString());
        params.append('limit', limit.toString());
        params.append('offset', pageOffset.toString());

        const response = await fetch(
          `/api/economic-calendar/upcoming?${params.toString()}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch economic calendar events');
        }

        const { data, meta } = await response.json();
        
        if (pageOffset === 0) {
          setEvents(data);
        } else {
          setEvents((prev) => [...prev, ...data]);
        }

        setTotalCount(meta.total_count);
        setHasMore(meta.has_next);
        setOffset(pageOffset);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    },
    [options, limit]
  );

  useEffect(() => {
    fetchEvents(0);
  }, [options, fetchEvents]);

  const loadMore = useCallback(() => {
    const nextOffset = offset + limit;
    fetchEvents(nextOffset);
  }, [offset, limit, fetchEvents]);

  return {
    events,
    loading,
    error,
    hasMore,
    loadMore,
    totalCount,
  };
};
```