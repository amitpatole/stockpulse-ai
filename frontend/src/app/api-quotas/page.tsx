```typescript
'use client';

import { useEffect, useState } from 'react';
import { QuotaCard } from '@/components/QuotaCard';
import { MetricsChart } from '@/components/MetricsChart';
import { useQuotaHistory, QuotaHistoryRecord } from '@/hooks/useQuotaHistory';

interface Quota {
  provider: string;
  quota_type: string;
  limit: number;
  used: number;
  percent_used: number;
  reset_at: string | null;
  status: 'normal' | 'warning' | 'critical';
  last_updated: string;
}

interface ApiQuotasResponse {
  data: Quota[];
  meta: {
    updated_at: string;
    total_providers: number;
  };
}

interface AnalyticsData {
  provider: string;
  peak_usage_percent: number;
  average_usage_percent: number;
  quota_types: string[];
  hours_analyzed: number;
  total_records: number;
}

export default function ApiQuotasPage() {
  const [quotas, setQuotas] = useState<Quota[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'current' | 'history'>('current');
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<Record<string, AnalyticsData>>({});
  const [sortBy, setSortBy] = useState<'usage' | 'provider' | 'status'>('usage');

  const { history: quotaHistory, loading: historyLoading } = useQuotaHistory(
    selectedProvider || undefined,
    48,
    30000
  );

  const fetchQuotas = async () => {
    try {
      const response = await fetch('/api/quotas');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: ApiQuotasResponse = await response.json();
      setQuotas(data.data);
      setLastUpdate(data.meta.updated_at);
      setError(null);

      // Fetch analytics for each provider
      const providers = [...new Set(data.data.map((q) => q.provider))];
      const analyticsData: Record<string, AnalyticsData> = {};

      for (const provider of providers) {
        try {
          const analyticsResponse = await fetch(`/api/quotas/${provider}/analytics?hours=48`);
          if (analyticsResponse.ok) {
            const analyticsJson = await analyticsResponse.json();
            analyticsData[provider] = analyticsJson.data;
          }
        } catch (err) {
          console.error(`Error fetching analytics for ${provider}:`, err);
        }
      }

      setAnalytics(analyticsData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load quotas';
      setError(message);
      console.error('Error fetching quotas:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchQuotas();

    // Poll every 30 seconds for updates
    const interval = setInterval(fetchQuotas, 30000);

    return () => clearInterval(interval);
  }, []);

  const getSortedQuotas = (quoatasToSort: Quota[]): Quota[] => {
    const sorted = [...quoatasToSort];
    switch (sortBy) {
      case 'usage':
        return sorted.sort((a, b) => b.percent_used - a.percent_used);
      case 'provider':
        return sorted.sort((a, b) => a.provider.localeCompare(b.provider));
      case 'status':
        const statusOrder = { critical: 0, warning: 1, normal: 2 };
        return sorted.sort(
          (a, b) =>
            statusOrder[a.status as keyof typeof statusOrder] -
            statusOrder[b.status as keyof typeof statusOrder]
        );
      default:
        return sorted;
    }
  };

  const sortedQuotas = getSortedQuotas(quotas);

  const criticalQuotas = quotas.filter((q) => q.status === 'critical');
  const warningQuotas = quotas.filter((q) => q.status === 'warning');
  const providers = [...new Set(quotas.map((q) => q.provider))];

  // Transform quota history into chart format
  const chartData = quotaHistory.map((record) => ({
    timestamp: record.recorded_at,
    metric_name: `${record.provider}_${record.quota_type}`,
    value: record.percent_used,
  }));

  if (loading && quotas.length === 0) {
    return (
      <div className="space-y-6 p-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">API Rate Limits</h1>
          <p className="mt-2 text-gray-600">
            Monitor API usage and quota across all data providers
          </p>
        </div>

        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-600">Loading quota data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">API Rate Limits</h1>
          <p className="mt-2 text-gray-600">
            Monitor API usage and quota across all data providers
          </p>
        </div>
        <button
          onClick={fetchQuotas}
          className="rounded-lg bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 transition-colors"
          title="Refresh quota data"
        >
          Refresh
        </button>
      </div>

      {/* Status information */}
      {lastUpdate && (
        <div className="rounded-lg bg-gray-100 px-4 py-3">
          <p className="text-sm text-gray-700">
            Last updated:{' '}
            <span className="font-semibold">
              {new Date(lastUpdate).toLocaleString()}
            </span>
            {' '}(Auto-refreshes every 30 seconds)
          </p>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
          <p className="text-sm text-red-800">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {/* Alert banner for critical quotas */}
      {criticalQuotas.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-4">
          <p className="text-sm font-semibold text-red-800 mb-2">
            ⚠️ {criticalQuotas.length} Critical Quota Alert{criticalQuotas.length !== 1 ? 's' : ''}
          </p>
          <p className="text-sm text-red-700 mb-3">
            The following quotas are at or above 80% usage:
          </p>
          <div className="flex flex-wrap gap-2">
            {criticalQuotas.map((q) => (
              <span
                key={`${q.provider}-${q.quota_type}`}
                className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-800"
              >
                {q.provider} - {q.quota_type} ({q.percent_used}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-8">
          <button
            onClick={() => setActiveTab('current')}
            className={`pb-4 px-1 border-b-2 font-semibold transition-colors ${
              activeTab === 'current'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Current Quotas
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`pb-4 px-1 border-b-2 font-semibold transition-colors ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            48-Hour History
          </button>
        </div>
      </div>

      {/* Current Quotas Tab */}
      {activeTab === 'current' && (
        <>
          {/* Sorting controls */}
          {quotas.length > 0 && (
            <div className="flex gap-4 items-center">
              <span className="text-sm font-semibold text-gray-700">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'usage' | 'provider' | 'status')}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="usage">Usage %</option>
                <option value="provider">Provider</option>
                <option value="status">Status</option>
              </select>
            </div>
          )}

          {/* Quotas grid */}
          {quotas.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-6 py-12 text-center">
              <p className="text-gray-600">No API quotas available</p>
              <button
                onClick={fetchQuotas}
                className="mt-4 text-blue-500 hover:underline"
              >
                Try again
              </button>
            </div>
          ) : (
            <div
              className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
              data-testid="quotas-grid"
            >
              {sortedQuotas.map((quota) => (
                <QuotaCard
                  key={`${quota.provider}-${quota.quota_type}`}
                  quota={quota}
                />
              ))}
            </div>
          )}

          {/* Summary stats */}
          {quotas.length > 0 && (
            <div className="mt-8 rounded-lg border border-gray-200 bg-white p-6">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">Summary</h2>
              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
                <div>
                  <p className="text-sm text-gray-600">Total Quotas</p>
                  <p className="text-2xl font-bold text-gray-900">{quotas.length}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Providers</p>
                  <p className="text-2xl font-bold text-gray-900">{providers.length}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Critical Status</p>
                  <p className="text-2xl font-bold text-red-600">{criticalQuotas.length}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg. Usage</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(
                      quotas.reduce((sum, q) => sum + q.percent_used, 0) / quotas.length
                    )}
                    %
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <>
          {/* Provider filter */}
          <div className="flex gap-4 items-center">
            <span className="text-sm font-semibold text-gray-700">Filter by provider:</span>
            <select
              value={selectedProvider || 'all'}
              onChange={(e) => setSelectedProvider(e.target.value === 'all' ? null : e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Providers</option>
              {providers.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          {/* Historical charts */}
          {historyLoading && quotaHistory.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
                <p className="mt-4 text-gray-600">Loading historical data...</p>
              </div>
            </div>
          ) : quotaHistory.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-6 py-12 text-center">
              <p className="text-gray-600">No historical data available</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Display analytics if available */}
              {selectedProvider && analytics[selectedProvider] && (
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    {selectedProvider} Analytics (48 hours)
                  </h3>
                  <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
                    <div>
                      <p className="text-sm text-gray-600">Peak Usage</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {analytics[selectedProvider].peak_usage_percent}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Average Usage</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {analytics[selectedProvider].average_usage_percent}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Quota Types</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {analytics[selectedProvider].quota_types.length}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Data Points</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {analytics[selectedProvider].total_records}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Chart for the selected provider or first provider */}
              {chartData.length > 0 && (
                <MetricsChart
                  data={chartData}
                  title={`${selectedProvider || 'Overall'} Usage Trend`}
                  metric_name={
                    selectedProvider
                      ? Object.keys(
                          quotaHistory.reduce(
                            (acc, record) => {
                              if (record.provider === selectedProvider) {
                                acc[`${record.provider}_${record.quota_type}`] = true;
                              }
                              return acc;
                            },
                            {} as Record<string, boolean>
                          )
                        )[0] || `${selectedProvider}_usage`
                      : 'usage'
                  }
                  yAxisLabel="Usage %"
                  color="#3b82f6"
                />
              )}

              {/* Historical data table */}
              <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Historical Records</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3 text-left font-semibold text-gray-700">Provider</th>
                        <th className="px-6 py-3 text-left font-semibold text-gray-700">Quota Type</th>
                        <th className="px-6 py-3 text-left font-semibold text-gray-700">Usage</th>
                        <th className="px-6 py-3 text-left font-semibold text-gray-700">Recorded</th>
                      </tr>
                    </thead>
                    <tbody>
                      {quotaHistory.slice(0, 50).map((record, idx) => (
                        <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                          <td className="px-6 py-3 text-gray-900 font-semibold">
                            {record.provider}
                          </td>
                          <td className="px-6 py-3 text-gray-600">{record.quota_type}</td>
                          <td className="px-6 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-500 h-2 rounded-full"
                                  style={{ width: `${Math.min(record.percent_used, 100)}%` }}
                                />
                              </div>
                              <span className="font-semibold text-gray-900 w-12">
                                {record.percent_used}%
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3 text-gray-600">
                            {new Date(record.recorded_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```