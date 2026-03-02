```typescript
import { useState, useEffect } from 'react';

export interface QuotaHistoryRecord {
  provider: string;
  quota_type: string;
  used: number;
  limit: number;
  percent_used: number;
  recorded_at: string;
}

export interface QuotaHistoryResponse {
  data: QuotaHistoryRecord[];
  meta: {
    time_range: string;
    records: number;
    provider: string;
  };
}

export function useQuotaHistory(
  provider?: string,
  hours: number = 48,
  pollInterval: number = 30000
) {
  const [history, setHistory] = useState<QuotaHistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      const params = new URLSearchParams();
      if (provider) params.append('provider', provider);
      params.append('hours', hours.toString());
      params.append('limit', '100');

      const response = await fetch(`/api/quotas/history?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: QuotaHistoryResponse = await response.json();
      setHistory(data.data);
      setLastUpdate(new Date().toISOString());
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load quota history';
      setError(message);
      console.error('Error fetching quota history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchHistory();

    // Poll for updates
    const interval = setInterval(fetchHistory, pollInterval);

    return () => clearInterval(interval);
  }, [provider, hours, pollInterval]);

  return {
    history,
    loading,
    error,
    lastUpdate,
    refetch: fetchHistory,
  };
}
```