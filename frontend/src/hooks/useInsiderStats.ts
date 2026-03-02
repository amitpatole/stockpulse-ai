```typescript
import { useState, useCallback, useEffect } from 'react';

export interface InsiderStats {
  cik: string;
  ticker: string;
  period_days: number;
  net_shares: number;
  buy_count: number;
  sell_count: number;
  total_buy_value: number;
  total_sell_value: number;
  sentiment_avg: number;
  insider_count: number;
  last_filing_date: string | null;
}

export interface UseInsiderStatsReturn {
  stats: InsiderStats | null;
  loading: boolean;
  error: string | null;
  period: 7 | 30 | 90;
  setPeriod: (period: 7 | 30 | 90) => void;
  refetch: () => Promise<void>;
}

export function useInsiderStats(cik: string): UseInsiderStatsReturn {
  const [stats, setStats] = useState<InsiderStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<7 | 30 | 90>(30);

  const refetch = useCallback(async () => {
    if (!cik) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/insiders/${cik}/stats?days=${period}`);

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const json = await response.json();

      if (json.data) {
        setStats(json.data);
      } else if (json.errors?.length > 0) {
        setError(json.errors[0]);
        setStats(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch insider stats');
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [cik, period]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return {
    stats,
    loading,
    error,
    period,
    setPeriod,
    refetch,
  };
}
```