/**
 * KPI Cards Component Tests
 *
 * Tests verify that:
 * - KPI cards render with correct data
 * - Loading states display skeletons
 * - Error handling is graceful
 * - Agent status calculations are correct
 * - All four KPI cards display properly
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import KPICards from '@/components/dashboard/KPICards';
import * as api from '@/lib/api';

// Mock hooks
jest.mock('@/hooks/useApi', () => ({
  useApi: jest.fn((fetcher, deps, opts) => {
    const stocksData = [
      { ticker: 'AAPL', name: 'Apple', active: true },
      { ticker: 'GOOGL', name: 'Google', active: true },
      { ticker: 'MSFT', name: 'Microsoft', active: false },
    ];

    const alertsData = [
      { id: 1, ticker: 'AAPL', type: 'price', message: 'Price alert', severity: 'high', created_at: '2026-03-03T10:00:00Z' },
      { id: 2, ticker: 'GOOGL', type: 'news', message: 'News alert', severity: 'medium', created_at: '2026-03-03T09:00:00Z' },
    ];

    const agentsData = [
      { name: 'researcher', status: 'running', enabled: true },
      { name: 'analyst', status: 'idle', enabled: true },
      { name: 'monitor', status: 'idle', enabled: true },
      { name: 'reporter', status: 'error', enabled: false },
    ];

    // Return based on function name
    if (fetcher.toString().includes('getStocks')) {
      return { data: stocksData, loading: false, error: null };
    }
    if (fetcher.toString().includes('getAlerts')) {
      return { data: alertsData, loading: false, error: null };
    }
    if (fetcher.toString().includes('getAgents')) {
      return { data: agentsData, loading: false, error: null };
    }

    return { data: null, loading: false, error: null };
  }),
}));

describe('KPI Cards', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================
  // Rendering & Display
  // ============================================================

  it('should render all four KPI cards', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText('Stocks Monitored')).toBeInTheDocument();
      expect(screen.getByText('Active Alerts')).toBeInTheDocument();
      expect(screen.getByText('Market Regime')).toBeInTheDocument();
      expect(screen.getByText('Agent Status')).toBeInTheDocument();
    });
  });

  it('should display correct number of active stocks', async () => {
    render(<KPICards />);

    await waitFor(() => {
      // Should show 2 active stocks (filter by active: true)
      expect(screen.getByText(/2/)).toBeInTheDocument();
    });
  });

  it('should display subtitle with total stocks count', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText(/3 total tracked/)).toBeInTheDocument();
    });
  });

  it('should display correct number of active alerts', async () => {
    render(<KPICards />);

    await waitFor(() => {
      // Should show 2 alerts
      const alertCards = screen.getAllByText(/2/);
      expect(alertCards.length).toBeGreaterThan(0);
    });
  });

  it('should display last 24 hours subtitle for alerts', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText('Last 24 hours')).toBeInTheDocument();
    });
  });

  it('should display market regime as Normal', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText('Normal')).toBeInTheDocument();
    });
  });

  it('should display regime assessment subtitle', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText('Assessed by regime agent')).toBeInTheDocument();
    });
  });

  it('should display correct agent status text', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText(/1 running, 2 idle, 1 error/)).toBeInTheDocument();
    });
  });

  // ============================================================
  // Loading States
  // ============================================================

  it('should show loading skeleton for stocks while loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getStocks')) {
        return { data: null, loading: true, error: null };
      }
      return { data: null, loading: false, error: null };
    });

    const { container } = render(<KPICards />);

    await waitFor(() => {
      const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  it('should show loading skeleton for alerts while loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getAlerts')) {
        return { data: null, loading: true, error: null };
      }
      return { data: null, loading: false, error: null };
    });

    const { container } = render(<KPICards />);

    await waitFor(() => {
      const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  it('should show loading skeleton for agents while loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getAgents')) {
        return { data: null, loading: true, error: null };
      }
      return { data: null, loading: false, error: null };
    });

    const { container } = render(<KPICards />);

    await waitFor(() => {
      const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  // ============================================================
  // Data Calculations
  // ============================================================

  it('should correctly count active stocks', async () => {
    render(<KPICards />);

    await waitFor(() => {
      // Should filter for active: true only
      const monitored = screen.getByText(/Stocks Monitored/).parentElement?.querySelector('[class*="text-2xl"]');
      expect(monitored?.textContent).toBe('2');
    });
  });

  it('should correctly count total stocks in subtitle', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText(/3 total tracked/)).toBeInTheDocument();
    });
  });

  it('should correctly count alert items', async () => {
    render(<KPICards />);

    await waitFor(() => {
      const alertsCard = screen.getByText('Active Alerts').parentElement;
      const value = alertsCard?.querySelector('[class*="text-2xl"]');
      expect(value?.textContent).toBe('2');
    });
  });

  it('should correctly categorize agent statuses', async () => {
    render(<KPICards />);

    await waitFor(() => {
      // Should show: 1 running, 2 idle, 1 error
      expect(screen.getByText(/1 running, 2 idle, 1 error/)).toBeInTheDocument();
    });
  });

  it('should not show error count when no errors', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getAgents')) {
        return {
          data: [
            { name: 'researcher', status: 'running', enabled: true },
            { name: 'analyst', status: 'idle', enabled: true },
            { name: 'monitor', status: 'idle', enabled: true },
          ],
          loading: false,
          error: null,
        };
      }
      return { data: null, loading: false, error: null };
    });

    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText(/1 running, 2 idle$/)).toBeInTheDocument();
    });
  });

  // ============================================================
  // Edge Cases
  // ============================================================

  it('should handle empty stocks array', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getStocks')) {
        return { data: [], loading: false, error: null };
      }
      return { data: null, loading: false, error: null };
    });

    render(<KPICards />);

    await waitFor(() => {
      const monitored = screen.getByText(/Stocks Monitored/).parentElement?.querySelector('[class*="text-2xl"]');
      expect(monitored?.textContent).toBe('0');
    });
  });

  it('should handle empty alerts array', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getAlerts')) {
        return { data: [], loading: false, error: null };
      }
      return { data: null, loading: false, error: null };
    });

    render(<KPICards />);

    await waitFor(() => {
      const alerts = screen.getByText(/Active Alerts/).parentElement?.querySelector('[class*="text-2xl"]');
      expect(alerts?.textContent).toBe('0');
    });
  });

  it('should handle empty agents array', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getAgents')) {
        return { data: [], loading: false, error: null };
      }
      return { data: null, loading: false, error: null };
    });

    render(<KPICards />);

    await waitFor(() => {
      const agents = screen.getByText(/Agent Status/).parentElement?.querySelector('[class*="text-2xl"]');
      expect(agents?.textContent).toBe('0');
    });
  });

  it('should handle null data gracefully', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: false,
      error: null,
    }));

    render(<KPICards />);

    await waitFor(() => {
      const monitored = screen.getByText(/Stocks Monitored/).parentElement?.querySelector('[class*="text-2xl"]');
      expect(monitored?.textContent).toBe('0');
    });
  });

  // ============================================================
  // Visual & Styling
  // ============================================================

  it('should render cards in grid layout', () => {
    const { container } = render(<KPICards />);

    const gridContainer = container.querySelector('[class*="grid"]');
    expect(gridContainer?.className).toContain('grid-cols-1');
    expect(gridContainer?.className).toContain('sm:grid-cols-2');
    expect(gridContainer?.className).toContain('xl:grid-cols-4');
  });

  it('should display icons for each card', async () => {
    const { container } = render(<KPICards />);

    await waitFor(() => {
      const svgs = container.querySelectorAll('svg');
      // Should have at least 4 icons (one per card)
      expect(svgs.length).toBeGreaterThanOrEqual(4);
    });
  });

  it('should have proper card styling', () => {
    const { container } = render(<KPICards />);

    const cards = container.querySelectorAll('[class*="rounded-xl"]');
    expect(cards.length).toBeGreaterThan(0);
  });

  // ============================================================
  // Integration Tests
  // ============================================================

  it('should render all data without loading state', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText('Normal')).toBeInTheDocument();
      expect(screen.getByText(/3 total tracked/)).toBeInTheDocument();
      expect(screen.getByText('Last 24 hours')).toBeInTheDocument();
      expect(screen.getByText(/1 running, 2 idle, 1 error/)).toBeInTheDocument();
    });

    // Should not have loading skeletons
    const { container } = render(<KPICards />);
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBe(0);
  });

  it('should handle all statuses for agents', async () => {
    render(<KPICards />);

    await waitFor(() => {
      expect(screen.getByText(/1 running/)).toBeInTheDocument();
      expect(screen.getByText(/2 idle/)).toBeInTheDocument();
      expect(screen.getByText(/1 error/)).toBeInTheDocument();
    });
  });

  it('should display subtitle only when not loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getStocks')) {
        return { data: null, loading: true, error: null };
      }
      return { data: null, loading: false, error: null };
    });

    render(<KPICards />);

    await waitFor(() => {
      // While loading, subtitle should not be visible
      expect(screen.queryByText(/3 total tracked/)).not.toBeInTheDocument();
    });
  });
});
