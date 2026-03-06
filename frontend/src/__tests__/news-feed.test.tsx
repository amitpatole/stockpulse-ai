/**
 * News Feed Component Tests
 *
 * Tests verify that:
 * - News articles are displayed with all metadata
 * - Loading and error states are handled
 * - Sentiment badges are shown correctly
 * - Time formatting works (relative time display)
 * - Links are properly configured
 * - Articles are scrollable
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import NewsFeed from '@/components/dashboard/NewsFeed';
import { SENTIMENT_COLORS } from '@/lib/types';

jest.mock('@/hooks/useApi', () => ({
  useApi: jest.fn((fetcher, deps, opts) => {
    const articlesData = [
      {
        id: 1,
        ticker: 'AAPL',
        title: 'Apple announces new AI features',
        source: 'TechNews',
        sentiment_label: 'positive',
        sentiment_score: 0.85,
        created_at: new Date(Date.now() - 5 * 60000).toISOString(), // 5 minutes ago
        url: 'https://technews.com/apple-ai',
      },
      {
        id: 2,
        ticker: 'GOOGL',
        title: 'Google faces regulatory challenges',
        source: 'Bloomberg',
        sentiment_label: 'negative',
        sentiment_score: -0.6,
        created_at: new Date(Date.now() - 2 * 3600000).toISOString(), // 2 hours ago
        url: 'https://bloomberg.com/google-regulation',
      },
      {
        id: 3,
        ticker: 'MSFT',
        title: 'Microsoft Q1 earnings beat expectations',
        source: 'Reuters',
        sentiment_label: 'positive',
        sentiment_score: 0.9,
        created_at: new Date(Date.now() - 24 * 3600000).toISOString(), // 1 day ago
        url: 'https://reuters.com/msft-earnings',
      },
      {
        id: 4,
        ticker: 'TSLA',
        title: 'Tesla stock price remains volatile',
        source: 'MarketWatch',
        sentiment_label: 'neutral',
        sentiment_score: 0.0,
        created_at: new Date(Date.now() - 30000).toISOString(), // 30 seconds ago
        url: 'https://marketwatch.com/tesla-volatile',
      },
    ];

    if (fetcher.toString().includes('getNews')) {
      return {
        data: articlesData,
        loading: false,
        error: null,
      };
    }

    return { data: null, loading: false, error: null };
  }),
}));

describe('News Feed', () => {
  // ============================================================
  // Rendering & Display
  // ============================================================

  it('should render news feed container', () => {
    render(<NewsFeed />);

    expect(screen.getByText('Recent News')).toBeInTheDocument();
  });

  it('should display all news articles', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      expect(screen.getByText('Apple announces new AI features')).toBeInTheDocument();
      expect(screen.getByText('Google faces regulatory challenges')).toBeInTheDocument();
      expect(screen.getByText('Microsoft Q1 earnings beat expectations')).toBeInTheDocument();
      expect(screen.getByText('Tesla stock price remains volatile')).toBeInTheDocument();
    });
  });

  it('should display ticker badge for each article', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      const tickers = screen.getAllByText(/AAPL|GOOGL|MSFT|TSLA/);
      expect(tickers.length).toBeGreaterThan(0);
    });
  });

  it('should display sentiment badge for each article', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      expect(screen.getByText('positive')).toBeInTheDocument();
      expect(screen.getByText('negative')).toBeInTheDocument();
      expect(screen.getByText('neutral')).toBeInTheDocument();
    });
  });

  it('should display source for each article', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      expect(screen.getByText('TechNews')).toBeInTheDocument();
      expect(screen.getByText('Bloomberg')).toBeInTheDocument();
      expect(screen.getByText('Reuters')).toBeInTheDocument();
      expect(screen.getByText('MarketWatch')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Links & Navigation
  // ============================================================

  it('should render links for each article', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
    });
  });

  it('should have correct href for article links', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      const appleLink = screen.getByRole('link', { name: /Apple announces/ });
      expect(appleLink).toHaveAttribute('href', 'https://technews.com/apple-ai');
    });
  });

  it('should open links in new tab', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('target', '_blank');
      });
    });
  });

  it('should have security attributes on external links', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      });
    });
  });

  // ============================================================
  // Time Display
  // ============================================================

  it('should display relative time for recent articles', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      // Article from 30 seconds ago should show "Just now"
      expect(screen.getByText('Just now')).toBeInTheDocument();
    });
  });

  it('should display minutes ago for articles within an hour', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      // Article from 5 minutes ago should show "5m ago"
      expect(screen.getByText('5m ago')).toBeInTheDocument();
    });
  });

  it('should display hours ago for articles within 24 hours', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      // Article from 2 hours ago should show "2h ago"
      expect(screen.getByText('2h ago')).toBeInTheDocument();
    });
  });

  it('should display days ago for older articles', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      // Article from 1 day ago should show "1d ago"
      expect(screen.getByText('1d ago')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Sentiment Styling
  // ============================================================

  it('should apply positive sentiment styling', async () => {
    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      const positiveElements = container.querySelectorAll('[class*="emerald"]');
      expect(positiveElements.length).toBeGreaterThan(0);
    });
  });

  it('should apply negative sentiment styling', async () => {
    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      const negativeElements = container.querySelectorAll('[class*="red"]');
      expect(negativeElements.length).toBeGreaterThan(0);
    });
  });

  it('should apply neutral sentiment styling', async () => {
    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      // Neutral uses slate colors
      const neutralElements = container.querySelectorAll('[class*="slate"]');
      expect(neutralElements.length).toBeGreaterThan(0);
    });
  });

  // ============================================================
  // Loading States
  // ============================================================

  it('should show loading skeletons while articles are loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: true,
      error: null,
    }));

    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  it('should not show empty state while loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: true,
      error: null,
    }));

    render(<NewsFeed />);

    expect(screen.queryByText('No news articles yet.')).not.toBeInTheDocument();
  });

  // ============================================================
  // Error States
  // ============================================================

  it('should show error message on API failure', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: false,
      error: 'Failed to load news',
    }));

    render(<NewsFeed />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load news')).toBeInTheDocument();
    });
  });

  it('should not show articles when error occurs', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: false,
      error: 'Network error',
    }));

    render(<NewsFeed />);

    expect(screen.queryByText('Apple announces new AI features')).not.toBeInTheDocument();
  });

  // ============================================================
  // Empty States
  // ============================================================

  it('should show empty state message when no articles', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: [],
      loading: false,
      error: null,
    }));

    render(<NewsFeed />);

    await waitFor(() => {
      expect(screen.getByText('No news articles yet.')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Article Structure
  // ============================================================

  it('should display article title as main content', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      const title = screen.getByText('Apple announces new AI features');
      expect(title).toBeInTheDocument();
      expect(title.closest('a')).toBeInTheDocument();
    });
  });

  it('should display all metadata in correct order', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      // Article should contain ticker, sentiment, source, and time
      const article = screen.getByText('Apple announces new AI features').closest('div');
      expect(article?.textContent).toContain('AAPL');
      expect(article?.textContent).toContain('positive');
      expect(article?.textContent).toContain('TechNews');
      expect(article?.textContent).toContain('ago');
    });
  });

  // ============================================================
  // Scrolling Container
  // ============================================================

  it('should have scrollable container for articles', () => {
    const { container } = render(<NewsFeed />);

    const scrollContainer = container.querySelector('[class*="max-h"]');
    expect(scrollContainer?.className).toContain('max-h-');
    expect(scrollContainer?.className).toContain('overflow-y-auto');
  });

  it('should have divider between articles', async () => {
    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      const dividers = container.querySelectorAll('[class*="divide-y"]');
      expect(dividers.length).toBeGreaterThan(0);
    });
  });

  // ============================================================
  // Visual Enhancements
  // ============================================================

  it('should have hover effect on articles', async () => {
    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      const articles = container.querySelectorAll('[class*="hover:"]');
      expect(articles.length).toBeGreaterThan(0);
    });
  });

  it('should display external link icon', async () => {
    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(0);
    });
  });

  it('should display clock icon for time', async () => {
    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      const svgs = container.querySelectorAll('svg');
      // Should have at least one icon per article (time icon)
      expect(svgs.length).toBeGreaterThanOrEqual(4);
    });
  });

  // ============================================================
  // Edge Cases
  // ============================================================

  it('should handle articles with very long titles', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: [
        {
          id: 1,
          ticker: 'AAPL',
          title: 'This is a very long article title that keeps going on and on and on without stopping to see how it renders and handles line clamping and text overflow scenarios properly across different screen sizes and viewport widths',
          source: 'News',
          sentiment_label: 'positive',
          sentiment_score: 0.8,
          created_at: new Date().toISOString(),
          url: 'https://example.com',
        },
      ],
      loading: false,
      error: null,
    }));

    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      // Should have line-clamp class
      const titleElement = container.querySelector('[class*="line-clamp"]');
      expect(titleElement).toBeInTheDocument();
    });
  });

  it('should handle mixed sentiment types', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      expect(screen.getByText('positive')).toBeInTheDocument();
      expect(screen.getByText('negative')).toBeInTheDocument();
      expect(screen.getByText('neutral')).toBeInTheDocument();
    });
  });

  it('should handle articles with same ticker', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: [
        {
          id: 1,
          ticker: 'AAPL',
          title: 'Apple Stock Goes Up',
          source: 'News1',
          sentiment_label: 'positive',
          sentiment_score: 0.8,
          created_at: new Date().toISOString(),
          url: 'https://example.com/1',
        },
        {
          id: 2,
          ticker: 'AAPL',
          title: 'Apple Stock Goes Down',
          source: 'News2',
          sentiment_label: 'negative',
          sentiment_score: -0.8,
          created_at: new Date().toISOString(),
          url: 'https://example.com/2',
        },
      ],
      loading: false,
      error: null,
    }));

    render(<NewsFeed />);

    await waitFor(() => {
      expect(screen.getByText('Apple Stock Goes Up')).toBeInTheDocument();
      expect(screen.getByText('Apple Stock Goes Down')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Integration Tests
  // ============================================================

  it('should render complete news feed with all features', async () => {
    render(<NewsFeed />);

    await waitFor(() => {
      // Should have header
      expect(screen.getByText('Recent News')).toBeInTheDocument();

      // Should have articles
      expect(screen.getByText('Apple announces new AI features')).toBeInTheDocument();

      // Should have metadata
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('positive')).toBeInTheDocument();
      expect(screen.getByText('TechNews')).toBeInTheDocument();

      // Should have links
      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
    });
  });

  it('should maintain scrollable feed with many articles', async () => {
    const manyArticles = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      ticker: `TICK${i}`,
      title: `Article ${i}`,
      source: 'News',
      sentiment_label: 'positive',
      sentiment_score: 0.5,
      created_at: new Date().toISOString(),
      url: `https://example.com/${i}`,
    }));

    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: manyArticles,
      loading: false,
      error: null,
    }));

    const { container } = render(<NewsFeed />);

    await waitFor(() => {
      // All articles should render (not just first few)
      expect(screen.getByText('Article 0')).toBeInTheDocument();
      expect(screen.getByText('Article 49')).toBeInTheDocument();
    });

    // Should have scroll container
    const scrollContainer = container.querySelector('[class*="overflow-y-auto"]');
    expect(scrollContainer).toBeInTheDocument();
  });
});
