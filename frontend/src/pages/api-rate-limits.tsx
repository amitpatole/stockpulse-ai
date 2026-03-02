'use client';

import React, { useState, useEffect } from 'react';
import { ProviderStatusCard } from '@/components/ProviderStatusCard';
import { UsageTimeSeries } from '@/components/UsageTimeSeries';
import { RateLimitGauge } from '@/components/RateLimitGauge';

interface RateLimitData {
  provider: string;
  limit_value: number;
  current_usage: number;
  usage_pct: number;
  reset_in_seconds: number;
  status: 'healthy' | 'warning' | 'critical' | 'error';
}

interface HistoryData {
  timestamp: string;
  usage_pct: number;
  call_count: number;
  errors: number;
}

export default function ApiRateLimitsPage() {
  const [providers, setProviders] = useState<RateLimitData[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch current rate limits
  const fetchRateLimits = async () => {
    try {
      const response = await fetch('/api/rate-limits');
      const result = await response.json();
      
      if (result.data) {
        setProviders(result.data);
        setLastUpdated(new Date());
      }
      setError(null);
    } catch (err) {
      setError('Failed to load rate limits');
      console.error('Error fetching rate limits:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch history for selected provider
  const fetchHistory = async (provider: string) => {
    try {
      const response = await fetch(
        `/api/rate-limits/${provider}/history?hours=24&interval=hourly`
      );
      const result = await response.json();
      
      if (result.data) {
        setHistory(result.data);
      }
    } catch (err) {
      console.error('Error fetching history:', err);
    }
  };

  // Initial fetch and polling
  useEffect(() => {
    fetchRateLimits();
    
    const interval = setInterval(fetchRateLimits, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  // Fetch history when provider selected
  useEffect(() => {
    if (selectedProvider) {
      fetchHistory(selectedProvider);
    }
  }, [selectedProvider]);

  const handleRefresh = async () => {
    setLoading(true);
    await fetchRateLimits();
  };

  if (loading && !providers.length) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="spinner" />
          <p className="mt-4 text-gray-600">Loading rate limits...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">API Rate Limits</h1>
            <p className="text-slate-600 mt-1">Monitor API usage and quotas across providers</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        {lastUpdated && (
          <p className="text-sm text-slate-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* Provider Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {providers.map((provider) => (
          <div
            key={provider.provider}
            onClick={() => setSelectedProvider(provider.provider)}
            className="cursor-pointer transform hover:scale-105 transition"
          >
            <ProviderStatusCard {...provider} />
          </div>
        ))}
      </div>

      {/* Gauges Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {providers.map((provider) => (
          <RateLimitGauge
            key={`gauge-${provider.provider}`}
            {...provider}
          />
        ))}
      </div>

      {/* Time Series Chart */}
      {selectedProvider && history.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">
            {selectedProvider} - 24 Hour Usage Trend
          </h2>
          <UsageTimeSeries
            provider={selectedProvider}
            data={history}
            hours={24}
            interval="hourly"
          />
        </div>
      )}
    </div>
  );
}