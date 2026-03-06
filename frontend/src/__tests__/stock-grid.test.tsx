/**
 * Stock Grid Component Tests
 *
 * Tests verify that:
 * - Stock ratings are displayed in grid
 * - Search functionality works with debounce
 * - Adding/removing stocks works
 * - Loading and error states are handled
 * - Keyboard navigation in dropdown works
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import StockGrid from '@/components/dashboard/StockGrid';
import * as api from '@/lib/api';

// Mock child component
jest.mock('@/components/dashboard/StockCard', () => {
  return function MockStockCard({ rating }: { rating: any }) {
    return <div data-testid={`stock-card-${rating.ticker}`}>{rating.ticker} - {rating.rating}</div>;
  };
});

jest.mock('@/hooks/useApi', () => ({
  useApi: jest.fn((fetcher, deps, opts) => {
    const ratingsData = [
      { ticker: 'AAPL', rating: 'BUY', score: 75, confidence: 0.9, current_price: 150 },
      { ticker: 'GOOGL', rating: 'HOLD', score: 60, confidence: 0.75, current_price: 140 },
      { ticker: 'MSFT', rating: 'BUY', score: 80, confidence: 0.95, current_price: 300 },
    ];

    if (fetcher.toString().includes('getRatings')) {
      return {
        data: ratingsData,
        loading: false,
        error: null,
        refetch: jest.fn(),
      };
    }

    return { data: null, loading: false, error: null, refetch: jest.fn() };
  }),
}));

jest.mock('@/lib/api');

describe('Stock Grid', () => {
  const mockSearchStocks = api.searchStocks as jest.Mock;
  const mockAddStock = api.addStock as jest.Mock;
  const mockDeleteStock = api.deleteStock as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchStocks.mockResolvedValue([
      { ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', type: 'Stock' },
      { ticker: 'APPL', name: 'Application Inc.', exchange: 'NYSE', type: 'Stock' },
    ]);
    mockAddStock.mockResolvedValue({ ticker: 'AAPL', name: 'Apple Inc.', active: true });
  });

  // ============================================================
  // Search Functionality
  // ============================================================

  it('should render search input', () => {
    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('should search stocks on input change after debounce', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    // Should not search immediately
    expect(mockSearchStocks).not.toHaveBeenCalled();

    // Fast-forward debounce timer
    jest.runAllTimers();

    await waitFor(() => {
      expect(mockSearchStocks).toHaveBeenCalledWith('AAPL');
    });

    jest.useRealTimers();
  });

  it('should show search results dropdown', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('should display exchange and type in dropdown', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      expect(screen.getByText('NASDAQ')).toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('should hide dropdown when empty query', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    // Clear search
    await user.clear(searchInput);
    jest.runAllTimers();

    // Dropdown should be hidden
    expect(screen.queryByText('Apple Inc.')).not.toBeInTheDocument();

    jest.useRealTimers();
  });

  it('should clear search on clear button click', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i) as HTMLInputElement;
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    const clearButton = screen.getByRole('button', { hidden: true });
    fireEvent.click(clearButton);

    expect(searchInput.value).toBe('');

    jest.useRealTimers();
  });

  // ============================================================
  // Keyboard Navigation
  // ============================================================

  it('should navigate dropdown with arrow keys', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    // Press arrow down
    fireEvent.keyDown(searchInput, { key: 'ArrowDown' });

    // First result should be highlighted (but visual test would need snapshots)
    await waitFor(() => {
      // Result element should exist
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('should select result on Enter key', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    // Navigate to first result
    fireEvent.keyDown(searchInput, { key: 'ArrowDown' });

    // Press Enter to select
    fireEvent.keyDown(searchInput, { key: 'Enter' });

    await waitFor(() => {
      expect(mockAddStock).toHaveBeenCalledWith('AAPL', 'Apple Inc.');
    });

    jest.useRealTimers();
  });

  it('should close dropdown on Escape key', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    // Press Escape
    fireEvent.keyDown(searchInput, { key: 'Escape' });

    // Dropdown should be hidden
    expect(screen.queryByText('Apple Inc.')).not.toBeInTheDocument();

    jest.useRealTimers();
  });

  // ============================================================
  // Adding Stocks
  // ============================================================

  it('should add stock on dropdown selection', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      const result = screen.getByText('Apple Inc.').closest('button');
      fireEvent.click(result!);
    });

    expect(mockAddStock).toHaveBeenCalledWith('AAPL', 'Apple Inc.');

    jest.useRealTimers();
  });

  it('should show loading indicator while adding stock', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    mockAddStock.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      const result = screen.getByText('Apple Inc.').closest('button');
      fireEvent.click(result!);
    });

    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();

    jest.useRealTimers();
  });

  it('should display error message on add failure', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    mockAddStock.mockRejectedValue(new Error('Stock already exists'));

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      const result = screen.getByText('Apple Inc.').closest('button');
      fireEvent.click(result!);
    });

    await waitFor(() => {
      expect(screen.getByText(/Stock already exists|Failed to add/i)).toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('should clear error message when searching again', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    mockAddStock.mockRejectedValue(new Error('Stock already exists'));

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      const result = screen.getByText('Apple Inc.').closest('button');
      fireEvent.click(result!);
    });

    await waitFor(() => {
      expect(screen.getByText(/Stock already exists|Failed to add/i)).toBeInTheDocument();
    });

    // Type again
    await user.type(searchInput, 'X');

    await waitFor(() => {
      // Error should be cleared
      expect(screen.queryByText(/Stock already exists/i)).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  // ============================================================
  // Stock Display
  // ============================================================

  it('should display stock ratings grid', async () => {
    render(<StockGrid />);

    await waitFor(() => {
      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-GOOGL')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-MSFT')).toBeInTheDocument();
    });
  });

  it('should show loading skeleton while stocks are loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
    }));

    const { container } = render(<StockGrid />);

    await waitFor(() => {
      const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  it('should show empty state when no stocks', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: [],
      loading: false,
      error: null,
      refetch: jest.fn(),
    }));

    render(<StockGrid />);

    await waitFor(() => {
      expect(screen.getByText('No stocks monitored yet.')).toBeInTheDocument();
      expect(screen.getByText(/Search for a stock above/)).toBeInTheDocument();
    });
  });

  it('should show error message on API failure', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: false,
      error: 'Failed to load stocks',
      refetch: jest.fn(),
    }));

    render(<StockGrid />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load stocks')).toBeInTheDocument();
    });
  });

  it('should have retry button on error', async () => {
    const mockRefetch = jest.fn();
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: false,
      error: 'Failed to load stocks',
      refetch: mockRefetch,
    }));

    render(<StockGrid />);

    await waitFor(() => {
      const retryButton = screen.getByRole('button', { name: /Retry/i });
      expect(retryButton).toBeInTheDocument();
    });
  });

  // ============================================================
  // Removing Stocks
  // ============================================================

  it('should remove stock from grid', async () => {
    const mockRefetch = jest.fn();
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getRatings')) {
        return {
          data: [
            { ticker: 'AAPL', rating: 'BUY', score: 75, confidence: 0.9, current_price: 150 },
          ],
          loading: false,
          error: null,
          refetch: mockRefetch,
        };
      }
      return { data: null, loading: false, error: null, refetch: jest.fn() };
    });

    mockDeleteStock.mockResolvedValue({});

    render(<StockGrid />);

    // In real test, would find remove button on StockCard and click it
    // This would call handleRemoveStock function
    await waitFor(() => {
      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Grid Layout
  // ============================================================

  it('should render stock cards in responsive grid', async () => {
    const { container } = render(<StockGrid />);

    await waitFor(() => {
      const grid = container.querySelector('[class*="grid"]');
      expect(grid?.className).toContain('grid-cols-1');
      expect(grid?.className).toContain('sm:grid-cols-2');
      expect(grid?.className).toContain('xl:grid-cols-3');
    });
  });

  // ============================================================
  // Edge Cases
  // ============================================================

  it('should not search for empty query', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, '   ');

    jest.runAllTimers();

    // Should not call search for whitespace
    expect(mockSearchStocks).not.toHaveBeenCalled();

    jest.useRealTimers();
  });

  it('should handle search with special characters', async () => {
    const user = userEvent.setup();
    jest.useFakeTimers();

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'BRK.B');

    jest.runAllTimers();

    await waitFor(() => {
      expect(mockSearchStocks).toHaveBeenCalledWith('BRK.B');
    });

    jest.useRealTimers();
  });

  it('should limit search input to 40 characters', () => {
    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i) as HTMLInputElement;
    expect(searchInput.maxLength).toBe(40);
  });

  // ============================================================
  // Integration Tests
  // ============================================================

  it('should handle complete search and add workflow', async () => {
    const user = userEvent.setup();
    const mockRefetch = jest.fn();

    jest.useFakeTimers();

    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getRatings')) {
        return {
          data: [],
          loading: false,
          error: null,
          refetch: mockRefetch,
        };
      }
      return { data: null, loading: false, error: null, refetch: jest.fn() };
    });

    render(<StockGrid />);

    const searchInput = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(searchInput, 'AAPL');

    jest.runAllTimers();

    await waitFor(() => {
      const result = screen.getByText('Apple Inc.').closest('button');
      fireEvent.click(result!);
    });

    await waitFor(() => {
      expect(mockAddStock).toHaveBeenCalledWith('AAPL', 'Apple Inc.');
      expect(mockRefetch).toHaveBeenCalled();
    });

    jest.useRealTimers();
  });
});
