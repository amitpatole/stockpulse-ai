```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { InsiderFilings } from '../InsiderFilings';

vi.mock('@/hooks/useInsiderActivity', () => ({
  useInsiderActivity: vi.fn(),
}));

describe('InsiderFilings Component', () => {
  const mockUseInsiderActivity = require('@/hooks/useInsiderActivity').useInsiderActivity;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    mockUseInsiderActivity.mockReturnValue({
      filings: [],
      meta: { total_count: 0, limit: 50, offset: 0, has_next: false },
      loading: true,
      error: null,
      filters: { ticker: null, transactionType: null, minDays: 30 },
      setTicker: vi.fn(),
      setTransactionType: vi.fn(),
      setMinDays: vi.fn(),
      setOffset: vi.fn(),
    });

    render(<InsiderFilings />);
    expect(screen.getByRole('progressbar', { hidden: true })).toBeDefined();
  });

  it('renders filings table with data', () => {
    mockUseInsiderActivity.mockReturnValue({
      filings: [
        {
          id: 1,
          ticker: 'AAPL',
          insider_name: 'Tim Cook',
          title: 'CEO',
          transaction_type: 'purchase',
          shares: 500,
          price: 185.25,
          value: 92625,
          filing_date: '2026-03-01T10:30:00Z',
          transaction_date: '2026-02-28',
          sentiment_score: 0.95,
          is_derivative: false,
          filing_url: 'https://sec.gov/filing',
        },
      ],
      meta: { total_count: 1, limit: 50, offset: 0, has_next: false },
      loading: false,
      error: null,
      filters: { ticker: null, transactionType: null, minDays: 30 },
      setTicker: vi.fn(),
      setTransactionType: vi.fn(),
      setMinDays: vi.fn(),
      setOffset: vi.fn(),
    });

    render(<InsiderFilings />);
    expect(screen.getByText('Tim Cook')).toBeDefined();
    expect(screen.getByText('CEO')).toBeDefined();
    expect(screen.getByText('500')).toBeDefined();
  });

  it('renders empty state when no filings', () => {
    mockUseInsiderActivity.mockReturnValue({
      filings: [],
      meta: { total_count: 0, limit: 50, offset: 0, has_next: false },
      loading: false,
      error: null,
      filters: { ticker: null, transactionType: null, minDays: 30 },
      setTicker: vi.fn(),
      setTransactionType: vi.fn(),
      setMinDays: vi.fn(),
      setOffset: vi.fn(),
    });

    render(<InsiderFilings />);
    expect(screen.getByText('No insider filings found')).toBeDefined();
  });

  it('filters by transaction type', () => {
    const mockSetTransactionType = vi.fn();
    mockUseInsiderActivity.mockReturnValue({
      filings: [],
      meta: { total_count: 0, limit: 50, offset: 0, has_next: false },
      loading: false,
      error: null,
      filters: { ticker: null, transactionType: null, minDays: 30 },
      setTicker: vi.fn(),
      setTransactionType: mockSetTransactionType,
      setMinDays: vi.fn(),
      setOffset: vi.fn(),
    });

    render(<InsiderFilings />);
    const select = screen.getByDisplayValue('All Types') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'purchase' } });
    expect(mockSetTransactionType).toHaveBeenCalledWith('purchase');
  });

  it('shows pagination controls', () => {
    mockUseInsiderActivity.mockReturnValue({
      filings: Array.from({ length: 50 }, (_, i) => ({
        id: i,
        ticker: 'AAPL',
        insider_name: `Insider ${i}`,
        title: 'Officer',
        transaction_type: 'purchase' as const,
        shares: 100,
        price: 150,
        value: 15000,
        filing_date: '2026-03-01T10:30:00Z',
        transaction_date: '2026-02-28',
        sentiment_score: 0.8,
        is_derivative: false,
        filing_url: 'https://sec.gov/filing',
      })),
      meta: { total_count: 150, limit: 50, offset: 0, has_next: true },
      loading: false,
      error: null,
      filters: { ticker: null, transactionType: null, minDays: 30 },
      setTicker: vi.fn(),
      setTransactionType: vi.fn(),
      setMinDays: vi.fn(),
      setOffset: vi.fn(),
    });

    render(<InsiderFilings />);
    expect(screen.getByText(/Showing 1 to 50 of 150/)).toBeDefined();
  });

  it('displays error message', () => {
    mockUseInsiderActivity.mockReturnValue({
      filings: [],
      meta: { total_count: 0, limit: 50, offset: 0, has_next: false },
      loading: false,
      error: 'Failed to fetch data',
      filters: { ticker: null, transactionType: null, minDays: 30 },
      setTicker: vi.fn(),
      setTransactionType: vi.fn(),
      setMinDays: vi.fn(),
      setOffset: vi.fn(),
    });

    render(<InsiderFilings />);
    expect(screen.getByText('Failed to fetch data')).toBeDefined();
  });
});
```