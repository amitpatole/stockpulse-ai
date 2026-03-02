```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';

export interface RateLimitData {
  provider: string;
  limit_value: number;
  current_usage: number;
  usage_pct: number;
  reset_in_seconds: number;
  status: 'healthy' | 'warning' | 'critical' | 'error';
}

export interface UseRateLimitsResult {
  providers: RateLimitData[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
}

/**
 * Hook for fetching and auto-polling API rate limits.
 * Auto-fetches every 30 seconds by default.
 */
export function useRateLimits(
  intervalMs: number = 30000
): UseRateLimitsResult {
  const [providers, setProviders] = useState<RateLimitData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchRateLimits = useCallback(async () => {
    try {
      const response = await fetch('/api/rate-limits');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const result = await response.json();

      if (result.data) {
        setProviders(result.data);
        setLastUpdated(new Date());
      }
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to load rate limits: ${message}`);
      console.error('Error fetching rate limits:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchRateLimits();
  }, [fetchRateLimits]);

  // Auto-polling
  useEffect(() => {
    if (intervalMs <= 0) return;

    const interval = setInterval(() => {
      fetchRateLimits();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs, fetchRateLimits]);

  return {
    providers,
    loading,
    error,
    lastUpdated,
    refetch: fetchRateLimits,
  };
}
```