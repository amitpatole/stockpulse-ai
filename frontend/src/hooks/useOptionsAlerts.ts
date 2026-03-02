/**
 * TickerPulse AI - useOptionsAlerts Hook
 * Provides access to options alerts with polling.
 */

import { useEffect, useState, useCallback } from 'react';

export interface OptionsAlert {
  id: number;
  ticker: string;
  flow_id?: number;
  alert_type: 'volume_spike' | 'unusual_ratio' | 'expiry_approaching';
  severity: 'low' | 'medium' | 'high';
  message: string;
  dismissed: number;
  created_at: string;
}

interface UseOptionsAlertsOptions {
  ticker?: string;
  severity?: 'low' | 'medium' | 'high';
  pollIntervalMs?: number;
  limit?: number;
}

interface UseOptionsAlertsResult {
  alerts: OptionsAlert[];
  unreadCount: number;
  isLoading: boolean;
  error?: string;
  dismissAlert: (alertId: number) => Promise<boolean>;
  refetch: () => Promise<void>;
}

export function useOptionsAlerts(
  options: UseOptionsAlertsOptions = {}
): UseOptionsAlertsResult {
  const {
    ticker,
    severity,
    pollIntervalMs = 5000,
    limit = 20,
  } = options;

  const [alerts, setAlerts] = useState<OptionsAlert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const fetchAlerts = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(undefined);

      const params = new URLSearchParams();
      if (ticker) params.append('ticker', ticker);
      if (severity) params.append('severity', severity);
      params.append('limit', limit.toString());
      params.append('offset', '0');

      const response = await fetch(`/api/options/alerts?${params}`);
      const data = await response.json();

      if (!response.ok || data.errors) {
        throw new Error(data.errors?.[0]?.message || 'Failed to fetch alerts');
      }

      setAlerts(data.data || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch alerts';
      setError(message);
      setAlerts([]);
    } finally {
      setIsLoading(false);
    }
  }, [ticker, severity, limit]);

  const dismissAlert = useCallback(
    async (alertId: number): Promise<boolean> => {
      try {
        const response = await fetch(`/api/options/alerts/${alertId}/dismiss`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
          throw new Error('Failed to dismiss alert');
        }

        // Update local state
        setAlerts((prev) =>
          prev.map((alert) =>
            alert.id === alertId ? { ...alert, dismissed: 1 } : alert
          )
        );

        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to dismiss alert';
        setError(message);
        return false;
      }
    },
    []
  );

  useEffect(() => {
    // Initial fetch
    fetchAlerts();

    // Poll at specified interval
    const interval = setInterval(fetchAlerts, pollIntervalMs);

    return () => clearInterval(interval);
  }, [fetchAlerts, pollIntervalMs]);

  // Count unread alerts
  const unreadCount = alerts.filter((a) => a.dismissed === 0).length;

  return {
    alerts,
    unreadCount,
    isLoading,
    error,
    dismissAlert,
    refetch: fetchAlerts,
  };
}