```typescript
/**
 * TickerPulse AI - Options Flow Hook
 * Fetches options flow data and manages real-time updates.
 */

import { useEffect, useCallback, useState } from 'react';
import { useOptionsFlow } from '@/context/OptionsFlowContext';
import type { OptionFlow, AlertSubscription } from '@/context/OptionsFlowContext';

interface FetchOptions {
  ticker?: string;
  flow_type?: string;
  min_anomaly_score?: number;
  limit?: number;
  offset?: number;
}

interface ApiResponse<T> {
  data: T;
  meta?: {
    total_count: number;
    limit: number;
    offset: number;
    has_next: boolean;
  };
  errors?: Array<{ code: string; message: string }>;
}

export function useOptionsFlowData(options: FetchOptions = {}) {
  const context = useOptionsFlow();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [hasMore, setHasMore] = useState(false);

  const fetchFlows = useCallback(async (opts = options) => {
    try {
      setIsLoading(true);
      setError(undefined);

      const params = new URLSearchParams();
      if (opts.ticker) params.append('ticker', opts.ticker);
      if (opts.flow_type) params.append('flow_type', opts.flow_type);
      if (opts.min_anomaly_score) params.append('min_anomaly_score', String(opts.min_anomaly_score));
      params.append('limit', String(opts.limit || 20));
      params.append('offset', String(opts.offset || 0));

      const response = await fetch(`/api/options/flows?${params}`);
      const data = (await response.json()) as ApiResponse<OptionFlow[]>;

      if (!response.ok || data.errors) {
        throw new Error(data.errors?.[0].message || 'Failed to fetch flows');
      }

      context.setFlows(data.data);
      setHasMore(data.meta?.has_next ?? false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch flows';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [context, options]);

  const fetchSubscriptions = useCallback(async () => {
    try {
      const response = await fetch('/api/options/alerts/subscriptions');
      const data = (await response.json()) as ApiResponse<AlertSubscription[]>;

      if (!response.ok || data.errors) {
        throw new Error(data.errors?.[0].message || 'Failed to fetch subscriptions');
      }

      context.setSubscriptions(data.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch subscriptions';
      console.error(message);
    }
  }, [context]);

  useEffect(() => {
    fetchFlows();
    fetchSubscriptions();
  }, [fetchFlows, fetchSubscriptions]);

  return {
    flows: context.flows,
    subscriptions: context.subscriptions,
    isLoading,
    error,
    hasMore,
    refetch: fetchFlows,
  };
}

export function useCreateSubscription() {
  const context = useOptionsFlow();
  const [isLoading, setIsLoading] = useState(false);

  const createSubscription = useCallback(
    async (subscription: Omit<AlertSubscription, 'id' | 'created_at'>) => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/options/alerts/subscriptions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(subscription),
        });

        const data = (await response.json()) as ApiResponse<AlertSubscription>;

        if (!response.ok || data.errors) {
          throw new Error(data.errors?.[0].message || 'Failed to create subscription');
        }

        context.addSubscription(data.data);
        return data.data;
      } finally {
        setIsLoading(false);
      }
    },
    [context]
  );

  return { createSubscription, isLoading };
}

export function useDeleteSubscription() {
  const context = useOptionsFlow();
  const [isLoading, setIsLoading] = useState(false);

  const deleteSubscription = useCallback(
    async (subscriptionId: number) => {
      try {
        setIsLoading(true);
        const response = await fetch(`/api/options/alerts/subscriptions/${subscriptionId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error('Failed to delete subscription');
        }

        context.removeSubscription(subscriptionId);
      } finally {
        setIsLoading(false);
      }
    },
    [context]
  );

  return { deleteSubscription, isLoading };
}
```