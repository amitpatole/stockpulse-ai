/**
 * TickerPulse AI - useOptionsFlows Hook
 * Provides real-time access to options flow data via polling.
 */

import { useEffect, useState, useCallback } from 'react';

export interface OptionsFlow {
  id: number;
  ticker: string;
  flow_type: 'call_spike' | 'put_spike' | 'unusual_volume';
  option_type: 'call' | 'put';
  strike_price: number;
  expiry_date: string;
  volume: number;
  open_interest: number;
  unusual_ratio: number;
  price_action: 'bullish' | 'bearish' | 'neutral';
  detected_at: string;
  created_at: string;
}

interface UseOptionsFlowsOptions {
  ticker?: string;
  minRatio?: number;
  flowType?: string;
  pollIntervalMs?: number;
}

interface UseOptionsFlowsResult {
  flows: OptionsFlow[];
  isLoading: boolean;
  error?: string;
  refetch: () => Promise<void>;
}

export function useOptionsFlows(
  options: UseOptionsFlowsOptions = {}
): UseOptionsFlowsResult {
  const {
    ticker,
    minRatio = 2.0,
    flowType,
    pollIntervalMs = 5000,
  } = options;

  const [flows, setFlows] = useState<OptionsFlow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const fetchFlows = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(undefined);

      const params = new URLSearchParams();
      if (ticker) params.append('ticker', ticker);
      if (minRatio) params.append('min_ratio', minRatio.toString());
      if (flowType) params.append('flow_type', flowType);
      params.append('limit', '50');
      params.append('offset', '0');

      const response = await fetch(`/api/options/flows?${params}`);
      const data = await response.json();

      if (!response.ok || data.errors) {
        throw new Error(data.errors?.[0]?.message || 'Failed to fetch flows');
      }

      setFlows(data.data || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch flows';
      setError(message);
      setFlows([]);
    } finally {
      setIsLoading(false);
    }
  }, [ticker, minRatio, flowType]);

  useEffect(() => {
    // Initial fetch
    fetchFlows();

    // Poll at specified interval
    const interval = setInterval(fetchFlows, pollIntervalMs);

    return () => clearInterval(interval);
  }, [fetchFlows, pollIntervalMs]);

  return { flows, isLoading, error, refetch: fetchFlows };
}