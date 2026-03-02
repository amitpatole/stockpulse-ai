```typescript
import { useState, useCallback, useEffect } from 'react';

export interface InsiderFiling {
  id: number;
  ticker: string;
  insider_name: string;
  title: string;
  transaction_type: 'purchase' | 'sale' | 'grant' | 'exercise';
  shares: number;
  price: number;
  value: number;
  filing_date: string;
  transaction_date: string;
  sentiment_score: number;
  is_derivative: boolean;
  filing_url: string;
}

export interface PaginationMeta {
  total_count: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

export interface UseInsiderActivityReturn {
  filings: InsiderFiling[];
  meta: PaginationMeta;
  loading: boolean;
  error: string | null;
  filters: {
    ticker: string | null;
    transactionType: string | null;
    minDays: number;
  };
  setTicker: (ticker: string | null) => void;
  setTransactionType: (type: string | null) => void;
  setMinDays: (days: number) => void;
  setLimit: (limit: number) => void;
  setOffset: (offset: number) => void;
  refetch: () => Promise<void>;
}

export function useInsiderActivity(): UseInsiderActivityReturn {
  const [filings, setFilings] = useState<InsiderFiling[]>([]);
  const [meta, setMeta] = useState<PaginationMeta>({
    total_count: 0,
    limit: 50,
    offset: 0,
    has_next: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    ticker: null as string | null,
    transactionType: null as string | null,
    minDays: 30,
  });
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (filters.ticker) params.append('ticker', filters.ticker);
      if (filters.transactionType && filters.transactionType !== 'all') {
        params.append('type', filters.transactionType);
      }
      params.append('min_days', filters.minDays.toString());
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());

      const response = await fetch(`/api/insiders/filings?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const json = await response.json();

      setFilings(json.data || []);
      setMeta(json.meta || {});

      if (json.errors?.length > 0) {
        setError(json.errors[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch insider activity');
      setFilings([]);
    } finally {
      setLoading(false);
    }
  }, [filters, limit, offset]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return {
    filings,
    meta,
    loading,
    error,
    filters,
    setTicker: (ticker) => setFilters((f) => ({ ...f, ticker })),
    setTransactionType: (type) => setFilters((f) => ({ ...f, transactionType: type })),
    setMinDays: (days) => setFilters((f) => ({ ...f, minDays: days })),
    setLimit,
    setOffset,
    refetch,
  };
}
```