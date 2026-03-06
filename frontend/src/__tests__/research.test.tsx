/**
 * Research Page Component Tests
 *
 * Tests verify that:
 * - Research briefs are displayed in list
 * - Brief filtering by ticker works
 * - Brief selection and detail view works
 * - Brief generation triggers API call
 * - Markdown content renders safely
 * - Loading and error states are handled
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ResearchPage from '@/app/research/page';
import * as api from '@/lib/api';

// Mock components
jest.mock('@/components/layout/Header', () => {
  return function MockHeader({ title, subtitle }: { title: string; subtitle: string }) {
    return <div data-testid="mock-header">{title} - {subtitle}</div>;
  };
});

// Mock hooks and API
jest.mock('@/hooks/useApi', () => ({
  useApi: jest.fn((fetcher, deps, opts) => {
    const briefsData = [
      {
        id: 1,
        ticker: 'AAPL',
        title: 'Apple Stock Analysis',
        content: '# Apple\n\nStrong buying signals detected.',
        agent_name: 'researcher',
        created_at: '2026-03-03T10:00:00Z',
        model_used: 'claude-opus',
      },
      {
        id: 2,
        ticker: 'GOOGL',
        title: 'Google Stock Analysis',
        content: '# Google\n\nModerate outlook.',
        agent_name: 'analyst',
        created_at: '2026-03-03T09:00:00Z',
        model_used: 'claude-opus',
      },
      {
        id: 3,
        ticker: 'AAPL',
        title: 'Apple Update',
        content: '# Apple Updated\n\nFurther analysis available.',
        agent_name: 'researcher',
        created_at: '2026-03-02T15:00:00Z',
        model_used: 'claude-sonnet',
      },
    ];

    // Mock getResearchBriefs
    if (fetcher.toString().includes('getResearchBriefs')) {
      return {
        data: briefsData,
        loading: false,
        error: null,
        refetch: jest.fn(),
      };
    }

    // Mock getStocks
    if (fetcher.toString().includes('getStocks')) {
      return {
        data: [
          { ticker: 'AAPL', name: 'Apple Inc.', active: true },
          { ticker: 'GOOGL', name: 'Alphabet Inc.', active: true },
          { ticker: 'MSFT', name: 'Microsoft Corporation', active: true },
        ],
        loading: false,
        error: null,
      };
    }

    return { data: null, loading: false, error: null, refetch: jest.fn() };
  }),
}));

jest.mock('@/lib/api');

describe('Research Page', () => {
  const mockGetResearchBriefs = api.getResearchBriefs as jest.Mock;
  const mockGenerateResearchBrief = api.generateResearchBrief as jest.Mock;
  const mockGetStocks = api.getStocks as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================
  // Rendering & Layout
  // ============================================================

  it('should render research page with header', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    });
    expect(screen.getByText(/AI-generated research analysis/i)).toBeInTheDocument();
  });

  it('should render briefs list section', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('Briefs')).toBeInTheDocument();
    });
  });

  it('should render toolbar with filter and generate button', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('Generate New Brief')).toBeInTheDocument();
    });

    // Should have filter dropdown
    const filterSelect = screen.getByDisplayValue('All Tickers');
    expect(filterSelect).toBeInTheDocument();
  });

  // ============================================================
  // Briefs List
  // ============================================================

  it('should display research briefs in list', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('Apple Stock Analysis')).toBeInTheDocument();
      expect(screen.getByText('Google Stock Analysis')).toBeInTheDocument();
    });
  });

  it('should show brief count', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText(/Briefs \(\d+\)/)).toBeInTheDocument();
    });
  });

  it('should display ticker badge for each brief', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const aaplBadges = screen.getAllByText('AAPL');
      expect(aaplBadges.length).toBeGreaterThan(0);
    });
  });

  it('should display agent name for each brief', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('researcher')).toBeInTheDocument();
      expect(screen.getByText('analyst')).toBeInTheDocument();
    });
  });

  it('should display formatted date for each brief', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      // Should display dates in readable format
      const dateTexts = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
      expect(dateTexts.length).toBeGreaterThan(0);
    });
  });

  it('should show message when no briefs exist', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getResearchBriefs')) {
        return { data: [], loading: false, error: null, refetch: jest.fn() };
      }
      return { data: null, loading: false, error: null };
    });

    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('No research briefs yet.')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Brief Selection & Detail View
  // ============================================================

  it('should select brief when clicking on list item', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Apple Stock Analysis').closest('button');
      expect(briefButton).toBeInTheDocument();
    });

    const briefButton = screen.getByText('Apple Stock Analysis').closest('button') as HTMLButtonElement;
    fireEvent.click(briefButton);

    // Brief should be highlighted
    expect(briefButton.className).toContain('border-blue-500');
  });

  it('should display brief details when selected', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Apple Stock Analysis').closest('button');
      fireEvent.click(briefButton!);
    });

    // Details should be visible
    await waitFor(() => {
      expect(screen.getByText('Apple Stock Analysis')).toBeInTheDocument();
      expect(screen.getByText(/researcher/)).toBeInTheDocument();
    });
  });

  it('should show empty state before brief selection', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('Select a brief to view its content')).toBeInTheDocument();
    });
  });

  it('should show brief title and ticker in detail view', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Apple Stock Analysis').closest('button');
      fireEvent.click(briefButton!);
    });

    await waitFor(() => {
      expect(screen.getByText('Apple Stock Analysis')).toBeInTheDocument();
      expect(screen.getAllByText('AAPL').length).toBeGreaterThan(0);
    });
  });

  it('should display model information when available', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Apple Stock Analysis').closest('button');
      fireEvent.click(briefButton!);
    });

    await waitFor(() => {
      expect(screen.getByText('claude-opus')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Filtering
  // ============================================================

  it('should filter briefs by ticker', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const filterSelect = screen.getByDisplayValue('All Tickers') as HTMLSelectElement;
      expect(filterSelect).toBeInTheDocument();
    });

    const filterSelect = screen.getByDisplayValue('All Tickers') as HTMLSelectElement;
    fireEvent.change(filterSelect, { target: { value: 'AAPL' } });

    // Should call API with ticker filter
    await waitFor(() => {
      expect(mockGetResearchBriefs).toHaveBeenCalledWith('AAPL');
    });
  });

  it('should populate filter dropdown with tickers from briefs', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const options = screen.getAllByRole('option') as HTMLOptionElement[];
      const tickerOptions = options.filter(opt => opt.value && !opt.selected);
      expect(tickerOptions.length).toBeGreaterThan(0);
    });
  });

  it('should show all available stock tickers in filter', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const filterSelect = screen.getByDisplayValue('All Tickers');
      const options = filterSelect.querySelectorAll('option');
      const hasAAPL = Array.from(options).some(opt => opt.textContent === 'AAPL');
      const hasGOOGL = Array.from(options).some(opt => opt.textContent === 'GOOGL');

      expect(hasAAPL).toBe(true);
      expect(hasGOOGL).toBe(true);
    });
  });

  it('should clear selected brief when filter changes', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Apple Stock Analysis').closest('button');
      fireEvent.click(briefButton!);
    });

    // Brief should be selected
    const briefButton = screen.getByText('Apple Stock Analysis').closest('button') as HTMLButtonElement;
    expect(briefButton.className).toContain('border-blue-500');

    // Change filter
    const filterSelect = screen.getByDisplayValue('All Tickers') as HTMLSelectElement;
    fireEvent.change(filterSelect, { target: { value: 'GOOGL' } });

    // Selected state should be cleared
    expect(briefButton.className).not.toContain('border-blue-500');
  });

  // ============================================================
  // Brief Generation
  // ============================================================

  it('should enable generate button', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const generateButton = screen.getByText('Generate New Brief');
      expect(generateButton).not.toBeDisabled();
    });
  });

  it('should generate brief with selected ticker filter', async () => {
    mockGenerateResearchBrief.mockResolvedValue({
      id: 4,
      ticker: 'AAPL',
      title: 'New Apple Brief',
      content: 'New brief content',
      agent_name: 'researcher',
      created_at: '2026-03-03T11:00:00Z',
    });

    render(<ResearchPage />);

    await waitFor(() => {
      const filterSelect = screen.getByDisplayValue('All Tickers') as HTMLSelectElement;
      fireEvent.change(filterSelect, { target: { value: 'AAPL' } });
    });

    const generateButton = screen.getByText('Generate New Brief');
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(mockGenerateResearchBrief).toHaveBeenCalledWith('AAPL');
    });
  });

  it('should disable button while generating', async () => {
    mockGenerateResearchBrief.mockImplementation(() => new Promise(() => {}));

    render(<ResearchPage />);

    await waitFor(() => {
      const generateButton = screen.getByText('Generate New Brief');
      fireEvent.click(generateButton);

      expect(generateButton).toBeDisabled();
    });
  });

  it('should show loading spinner while generating', async () => {
    mockGenerateResearchBrief.mockImplementation(() => new Promise(() => {}));

    const { container } = render(<ResearchPage />);

    await waitFor(() => {
      const generateButton = screen.getByText('Generate New Brief');
      fireEvent.click(generateButton);
    });

    await waitFor(() => {
      const spinner = container.querySelector('[class*="animate-spin"]');
      expect(spinner).toBeInTheDocument();
    });
  });

  it('should handle generation errors gracefully', async () => {
    mockGenerateResearchBrief.mockRejectedValue(new Error('Generation failed'));

    render(<ResearchPage />);

    await waitFor(() => {
      const generateButton = screen.getByText('Generate New Brief');
      fireEvent.click(generateButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/Generation failed|Failed to generate/i)).toBeInTheDocument();
    });
  });

  // ============================================================
  // Markdown Content Rendering
  // ============================================================

  it('should render markdown content safely', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Apple Stock Analysis').closest('button');
      fireEvent.click(briefButton!);
    });

    await waitFor(() => {
      // Content should be rendered
      const content = screen.getByText(/Strong buying signals/i);
      expect(content).toBeInTheDocument();
    });
  });

  it('should format markdown headers', async () => {
    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Apple Stock Analysis').closest('button');
      fireEvent.click(briefButton!);
    });

    // Should have rendered content with text "Apple"
    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });
  });

  it('should prevent XSS in markdown content', async () => {
    // Brief with potentially malicious content
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getResearchBriefs')) {
        return {
          data: [
            {
              id: 1,
              ticker: 'TEST',
              title: 'Test Brief',
              content: '<script>alert("XSS")</script>Regular content',
              agent_name: 'test',
              created_at: '2026-03-03T10:00:00Z',
            },
          ],
          loading: false,
          error: null,
          refetch: jest.fn(),
        };
      }
      return { data: null, loading: false, error: null };
    });

    const { container } = render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Test Brief').closest('button');
      fireEvent.click(briefButton!);
    });

    // Should not contain script tag
    expect(container.innerHTML).not.toContain('<script>');
    expect(container.innerHTML).not.toContain('alert');
  });

  // ============================================================
  // Loading States
  // ============================================================

  it('should show loading skeletons while briefs are loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getResearchBriefs')) {
        return { data: null, loading: true, error: null, refetch: jest.fn() };
      }
      return { data: null, loading: false, error: null };
    });

    const { container } = render(<ResearchPage />);

    await waitFor(() => {
      const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  it('should show error message when API fails', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getResearchBriefs')) {
        return { data: null, loading: false, error: 'Failed to load briefs', refetch: jest.fn() };
      }
      return { data: null, loading: false, error: null };
    });

    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load briefs')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Edge Cases
  // ============================================================

  it('should handle briefs with missing optional fields', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getResearchBriefs')) {
        return {
          data: [
            {
              id: 1,
              ticker: 'TEST',
              title: 'Test Brief',
              content: 'Content',
              agent_name: 'test',
              created_at: '2026-03-03T10:00:00Z',
              // model_used is missing
            },
          ],
          loading: false,
          error: null,
          refetch: jest.fn(),
        };
      }
      return { data: null, loading: false, error: null };
    });

    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Test Brief').closest('button');
      fireEvent.click(briefButton!);
    });

    // Should not crash and should display brief
    expect(screen.getByText('Test Brief')).toBeInTheDocument();
  });

  it('should display content without hanging on very long briefs', async () => {
    const longContent = '# Header\n' + 'Line of text\n'.repeat(1000);

    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getResearchBriefs')) {
        return {
          data: [
            {
              id: 1,
              ticker: 'LONG',
              title: 'Long Brief',
              content: longContent,
              agent_name: 'test',
              created_at: '2026-03-03T10:00:00Z',
            },
          ],
          loading: false,
          error: null,
          refetch: jest.fn(),
        };
      }
      return { data: null, loading: false, error: null };
    });

    render(<ResearchPage />);

    await waitFor(() => {
      const briefButton = screen.getByText('Long Brief').closest('button');
      fireEvent.click(briefButton!);
    });

    // Should render without issues
    expect(screen.getByText('Long Brief')).toBeInTheDocument();
  });

  it('should handle ticker names with special characters', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation((fetcher) => {
      if (fetcher.toString().includes('getResearchBriefs')) {
        return {
          data: [
            {
              id: 1,
              ticker: 'BRK.B',
              title: 'Berkshire Brief',
              content: 'Content',
              agent_name: 'test',
              created_at: '2026-03-03T10:00:00Z',
            },
          ],
          loading: false,
          error: null,
          refetch: jest.fn(),
        };
      }
      return { data: null, loading: false, error: null };
    });

    render(<ResearchPage />);

    await waitFor(() => {
      expect(screen.getByText('BRK.B')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Integration Tests
  // ============================================================

  it('should handle complete workflow: filter -> select -> view', async () => {
    render(<ResearchPage />);

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText('Apple Stock Analysis')).toBeInTheDocument();
    });

    // Filter by ticker
    const filterSelect = screen.getByDisplayValue('All Tickers') as HTMLSelectElement;
    fireEvent.change(filterSelect, { target: { value: 'AAPL' } });

    // API should be called with filter
    await waitFor(() => {
      expect(mockGetResearchBriefs).toHaveBeenCalledWith('AAPL');
    });

    // Click brief to view details
    const briefButton = screen.getByText('Apple Stock Analysis').closest('button') as HTMLButtonElement;
    fireEvent.click(briefButton);

    // Details should be visible
    await waitFor(() => {
      expect(briefButton.className).toContain('border-blue-500');
    });
  });
});
