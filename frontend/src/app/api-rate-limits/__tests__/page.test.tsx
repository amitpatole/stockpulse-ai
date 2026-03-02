"""
E2E tests for API Rate Limits dashboard page
Tests rendering, data loading, user interactions, and state updates.
"""

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ApiRateLimitsPage from '../page';

// Mock the fetch API
global.fetch = vi.fn();

// Mock child components
vi.mock('@/components/ProviderStatusCard', () => ({
  ProviderStatusCard: ({ provider, status }: any) => (
    <div data-testid={`provider-card-${provider}`}>{provider} - {status}</div>
  )
}));

vi.mock('@/components/RateLimitGauge', () => ({
  RateLimitGauge: ({ provider }: any) => (
    <div data-testid={`gauge-${provider}`}>{provider} Gauge</div>
  )
}));

vi.mock('@/components/UsageTimeSeries', () => ({
  UsageTimeSeries: ({ provider, data }: any) => (
    <div data-testid={`timeseries-${provider}`}>{provider} - {data.length} points</div>
  )
}));

describe('ApiRateLimitsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header with title and refresh button', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      json: async () => ({ data: [] })
    });

    render(<ApiRateLimitsPage />);

    expect(screen.getByText('API Rate Limits')).toBeInTheDocument();
    expect(screen.getByText('Monitor API usage and quotas across providers')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
  });

  it('displays loading state on initial load', () => {
    (global.fetch as any).mockImplementationOnce(
      () => new Promise(resolve => setTimeout(() => resolve({ json: async () => ({ data: [] }) }), 100))
    );

    render(<ApiRateLimitsPage />);

    expect(screen.getByText(/Loading rate limits/)).toBeInTheDocument();
  });

  it('loads and displays provider data', async () => {
    const mockData = {
      data: [
        {
          provider: 'CoinGecko',
          limit_value: 50,
          current_usage: 25,
          usage_pct: 50,
          reset_in_seconds: 3600,
          status: 'healthy'
        },
        {
          provider: 'TradingView',
          limit_value: 3000,
          current_usage: 1200,
          usage_pct: 40,
          reset_in_seconds: 86400,
          status: 'healthy'
        }
      ]
    };

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => mockData
    });

    render(<ApiRateLimitsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('provider-card-CoinGecko')).toBeInTheDocument();
      expect(screen.getByTestId('provider-card-TradingView')).toBeInTheDocument();
    });
  });

  it('displays gauge components for each provider', async () => {
    const mockData = {
      data: [
        {
          provider: 'CoinGecko',
          limit_value: 50,
          current_usage: 25,
          usage_pct: 50,
          reset_in_seconds: 3600,
          status: 'healthy'
        }
      ]
    };

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => mockData
    });

    render(<ApiRateLimitsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('gauge-CoinGecko')).toBeInTheDocument();
    });
  });

  it('fetches and displays history when provider is selected', async () => {
    const mockProviders = {
      data: [
        {
          provider: 'CoinGecko',
          limit_value: 50,
          current_usage: 25,
          usage_pct: 50,
          reset_in_seconds: 3600,
          status: 'healthy'
        }
      ]
    };

    const mockHistory = {
      data: [
        {
          timestamp: '2026-03-02T09:00:00Z',
          usage_pct: 25,
          call_count: 12,
          errors: 0
        },
        {
          timestamp: '2026-03-02T10:00:00Z',
          usage_pct: 38,
          call_count: 19,
          errors: 0
        }
      ]
    };

    (global.fetch as any)
      .mockResolvedValueOnce({ json: async () => mockProviders })
      .mockResolvedValueOnce({ json: async () => mockHistory });

    render(<ApiRateLimitsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('provider-card-CoinGecko')).toBeInTheDocument();
    });

    // Click provider card
    await userEvent.click(screen.getByTestId('provider-card-CoinGecko'));

    await waitFor(() => {
      expect(screen.getByTestId('timeseries-CoinGecko')).toBeInTheDocument();
    });
  });

  it('polls for updates every 30 seconds', async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => ({ data: [] })
    });

    vi.useFakeTimers();
    render(<ApiRateLimitsPage />);

    expect(global.fetch).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(30000);
    expect(global.fetch).toHaveBeenCalledTimes(2);

    vi.advanceTimersByTime(30000);
    expect(global.fetch).toHaveBeenCalledTimes(3);

    vi.useRealTimers();
  });

  it('handles refresh button click', async () => {
    const mockData = {
      data: [
        {
          provider: 'CoinGecko',
          limit_value: 50,
          current_usage: 25,
          usage_pct: 50,
          reset_in_seconds: 3600,
          status: 'healthy'
        }
      ]
    };

    (global.fetch as any).mockResolvedValue({
      json: async () => mockData
    });

    render(<ApiRateLimitsPage />);

    await waitFor(() => {
      expect(screen.getByText('CoinGecko')).toBeInTheDocument();
    });

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await userEvent.click(refreshButton);

    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('displays last updated timestamp', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      json: async () => ({ data: [] })
    });

    render(<ApiRateLimitsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  it('displays error message when API fails', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<ApiRateLimitsPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load rate limits')).toBeInTheDocument();
    });
  });
});