import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NewsFeed from '../NewsFeed';

// Mock the useApi hook
jest.mock('@/hooks/useApi', () => ({
  useApi: jest.fn(),
}));

// Mock the getNews API function
jest.mock('@/lib/api', () => ({
  getNews: jest.fn(),
}));

// Mock the KeyboardShortcutsProvider context
jest.mock('@/components/layout/KeyboardShortcutsProvider', () => ({
  useKeyboardShortcutsContext: () => ({
    registerNewsFeed: jest.fn(),
  }),
}));

import { useApi } from '@/hooks/useApi';

const mockUseApi = useApi as jest.MockedFunction<typeof useApi>;

describe('NewsFeed Component', () => {
  const mockArticles = [
    {
      id: '1',
      title: 'Tech Stock Rises',
      url: 'https://example.com/1',
      ticker: 'TECH',
      sentiment_label: 'positive',
      source: 'TechNews',
      created_at: '2024-01-01T10:00:00',
    },
    {
      id: '2',
      title: 'Market Volatility',
      url: 'https://example.com/2',
      ticker: 'SPY',
      sentiment_label: 'negative',
      source: 'FinancialTimes',
      created_at: '2024-01-01T09:00:00',
    },
    {
      id: '3',
      title: 'Earnings Beat',
      url: 'https://example.com/3',
      ticker: 'AAPL',
      sentiment_label: 'positive',
      source: 'Bloomberg',
      created_at: '2024-01-01T08:00:00',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApi.mockReturnValue({
      data: mockArticles,
      loading: false,
      error: null,
    });
  });

  describe('Rendering', () => {
    it('should render news feed panel', () => {
      render(<NewsFeed />);
      expect(screen.getByText('Recent News')).toBeInTheDocument();
    });

    it('should render articles with correct ARIA roles', () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');
      expect(feedContainer).toBeInTheDocument();
      expect(feedContainer).toHaveAttribute('aria-label', 'Recent news');
    });

    it('should render each article with article role', () => {
      render(<NewsFeed />);
      const articles = screen.getAllByRole('article');
      expect(articles).toHaveLength(mockArticles.length);
    });

    it('should display article titles', () => {
      render(<NewsFeed />);
      mockArticles.forEach(article => {
        expect(screen.getByText(article.title)).toBeInTheDocument();
      });
    });

    it('should display article metadata (ticker, sentiment, source, time)', () => {
      render(<NewsFeed />);
      expect(screen.getByText('TECH')).toBeInTheDocument();
      expect(screen.getByText('TechNews')).toBeInTheDocument();
      expect(screen.getByText('positive')).toBeInTheDocument();
    });

    it('should render external link icons', () => {
      const { container } = render(<NewsFeed />);
      const externalLinkIcons = container.querySelectorAll('svg');
      expect(externalLinkIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Loading State', () => {
    it('should show loading skeletons when data is loading', () => {
      mockUseApi.mockReturnValue({
        data: null,
        loading: true,
        error: null,
      });

      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');
      expect(feedContainer).toHaveAttribute('aria-busy', 'true');
    });

    it('should display 5 skeleton items during loading', () => {
      mockUseApi.mockReturnValue({
        data: null,
        loading: true,
        error: null,
      });

      const { container } = render(<NewsFeed />);
      const skeletonItems = container.querySelectorAll('.animate-pulse');
      expect(skeletonItems).toHaveLength(5);
    });
  });

  describe('Error State', () => {
    it('should display error message when error occurs', () => {
      mockUseApi.mockReturnValue({
        data: null,
        loading: false,
        error: 'Failed to fetch news',
      });

      render(<NewsFeed />);
      expect(screen.getByText('Failed to fetch news')).toBeInTheDocument();
    });

    it('should display error in red color', () => {
      mockUseApi.mockReturnValue({
        data: null,
        loading: false,
        error: 'Network error',
      });

      render(<NewsFeed />);
      const errorElement = screen.getByText('Network error');
      expect(errorElement).toHaveClass('text-red-400');
    });
  });

  describe('Empty State', () => {
    it('should display empty message when no articles', () => {
      mockUseApi.mockReturnValue({
        data: [],
        loading: false,
        error: null,
      });

      render(<NewsFeed />);
      expect(screen.getByText('No news articles yet.')).toBeInTheDocument();
    });
  });

  describe('Article Links', () => {
    it('should render anchor tags for each article', () => {
      render(<NewsFeed />);
      const links = screen.getAllByRole('link');
      expect(links.length).toBe(mockArticles.length);
    });

    it('should open articles in new tab', () => {
      render(<NewsFeed />);
      const links = screen.getAllByRole('link');
      links.forEach((link, i) => {
        expect(link).toHaveAttribute('href', mockArticles[i].url);
        expect(link).toHaveAttribute('target', '_blank');
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      });
    });

    it('should have tabIndex -1 to prevent keyboard focus on anchors', () => {
      render(<NewsFeed />);
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('tabIndex', '-1');
      });
    });
  });

  describe('Keyboard Navigation - Arrow Keys', () => {
    it('should navigate down with arrow key', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      // Focus the feed
      feedContainer.focus();

      // Navigate down
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should navigate up with arrow key', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });
      fireEvent.keyDown(feedContainer, { key: 'ArrowUp' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should wrap from last to first with arrow down', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();

      // Navigate to last article
      for (let i = 0; i < mockArticles.length; i++) {
        fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });
      }

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[mockArticles.length - 1]).toHaveAttribute('aria-current', 'true');
      });

      // Wrap to first
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should wrap from first to last with arrow up', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();

      fireEvent.keyDown(feedContainer, { key: 'ArrowUp' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[mockArticles.length - 1]).toHaveAttribute('aria-current', 'true');
      });
    });
  });

  describe('Keyboard Navigation - Home/End', () => {
    it('should jump to first article with Home key', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'End' });
      fireEvent.keyDown(feedContainer, { key: 'Home' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should jump to last article with End key', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'End' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[mockArticles.length - 1]).toHaveAttribute('aria-current', 'true');
      });
    });
  });

  describe('Keyboard Navigation - PageDown/PageUp', () => {
    it('should advance by 5 items with PageDown', async () => {
      const manyArticles = Array.from({ length: 15 }, (_, i) => ({
        ...mockArticles[0],
        id: String(i),
        title: `Article ${i}`,
      }));

      mockUseApi.mockReturnValue({
        data: manyArticles,
        loading: false,
        error: null,
      });

      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'PageDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[5]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should retreat by 5 items with PageUp', async () => {
      const manyArticles = Array.from({ length: 15 }, (_, i) => ({
        ...mockArticles[0],
        id: String(i),
        title: `Article ${i}`,
      }));

      mockUseApi.mockReturnValue({
        data: manyArticles,
        loading: false,
        error: null,
      });

      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'End' });
      fireEvent.keyDown(feedContainer, { key: 'PageUp' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[9]).toHaveAttribute('aria-current', 'true');
      });
    });
  });

  describe('Keyboard Navigation - Enter Key', () => {
    it('should activate navigation on Enter key', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'Enter' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });
    });
  });

  describe('Keyboard Navigation - Escape Key', () => {
    it('should release focus on Escape key', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });

      fireEvent.keyDown(feedContainer, { key: 'Escape' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        articles.forEach(article => {
          expect(article).not.toHaveAttribute('aria-current');
        });
      });
    });
  });

  describe('Visual Focus Indicator', () => {
    it('should apply focus ring style to focused article', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveClass('ring-2', 'ring-blue-500');
      });
    });

    it('should apply background highlight to focused article', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveClass('bg-slate-700/20');
      });
    });

    it('should remove focus ring when focus is released', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveClass('ring-2');
      });

      fireEvent.keyDown(feedContainer, { key: 'Escape' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).not.toHaveClass('ring-2');
      });
    });
  });

  describe('Article Refresh Behavior', () => {
    it('should preserve focus index when articles refresh', async () => {
      const { rerender } = render(<NewsFeed />);
      let feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });

      // Simulate refresh with same articles
      mockUseApi.mockReturnValue({
        data: mockArticles,
        loading: false,
        error: null,
      });

      rerender(<NewsFeed />);
      feedContainer = screen.getByRole('feed');

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should clamp focus index when articles list shrinks', async () => {
      const { rerender } = render(<NewsFeed />);
      let feedContainer = screen.getByRole('feed');

      feedContainer.focus();

      // Navigate to last article
      for (let i = 0; i < mockArticles.length; i++) {
        fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });
      }

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[2]).toHaveAttribute('aria-current', 'true');
      });

      // Simulate refresh with fewer articles
      const fewerArticles = mockArticles.slice(0, 2);
      mockUseApi.mockReturnValue({
        data: fewerArticles,
        loading: false,
        error: null,
      });

      rerender(<NewsFeed />);
      feedContainer = screen.getByRole('feed');

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles.length).toBe(2);
        expect(articles[1]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should clear focus when all articles are removed', async () => {
      const { rerender } = render(<NewsFeed />);
      let feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });

      // Simulate refresh with no articles
      mockUseApi.mockReturnValue({
        data: [],
        loading: false,
        error: null,
      });

      rerender(<NewsFeed />);
      feedContainer = screen.getByRole('feed');

      await waitFor(() => {
        expect(screen.getByText('No news articles yet.')).toBeInTheDocument();
      });
    });
  });

  describe('Container ARIA Attributes', () => {
    it('should have role="feed"', () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');
      expect(feedContainer).toHaveAttribute('role', 'feed');
    });

    it('should have aria-label', () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');
      expect(feedContainer).toHaveAttribute('aria-label', 'Recent news');
    });

    it('should have aria-busy=true during loading', () => {
      mockUseApi.mockReturnValue({
        data: null,
        loading: true,
        error: null,
      });

      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');
      expect(feedContainer).toHaveAttribute('aria-busy', 'true');
    });

    it('should have aria-busy=false when not loading', () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');
      expect(feedContainer).toHaveAttribute('aria-busy', 'false');
    });

    it('should have tabIndex=0 for focus', () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');
      expect(feedContainer).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Article Item ARIA Attributes', () => {
    it('should have role="article"', () => {
      render(<NewsFeed />);
      const articles = screen.getAllByRole('article');
      articles.forEach(article => {
        expect(article).toHaveAttribute('role', 'article');
      });
    });

    it('should have aria-label with article title', () => {
      render(<NewsFeed />);
      mockArticles.forEach(article => {
        const articleElements = screen.getAllByRole('article');
        const found = articleElements.some(el => el.getAttribute('aria-label') === article.title);
        expect(found).toBe(true);
      });
    });

    it('should have aria-current when focused', async () => {
      render(<NewsFeed />);
      const feedContainer = screen.getByRole('feed');

      feedContainer.focus();
      fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });

      await waitFor(() => {
        const articles = screen.getAllByRole('article');
        expect(articles[0]).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should not have aria-current when not focused', () => {
      render(<NewsFeed />);
      const articles = screen.getAllByRole('article');
      articles.forEach(article => {
        if (!article.hasAttribute('aria-current')) {
          expect(article.getAttribute('aria-current')).toBeNull();
        }
      });
    });

    it('should have tabIndex=-1 to prevent individual focus', () => {
      render(<NewsFeed />);
      const articles = screen.getAllByRole('article');
      articles.forEach(article => {
        expect(article).toHaveAttribute('tabIndex', '-1');
      });
    });
  });

  describe('Time Display', () => {
    it('should display "Just now" for very recent articles', () => {
      const now = new Date();
      const recentArticle = {
        ...mockArticles[0],
        created_at: now.toISOString(),
      };

      mockUseApi.mockReturnValue({
        data: [recentArticle],
        loading: false,
        error: null,
      });

      render(<NewsFeed />);
      expect(screen.getByText('Just now')).toBeInTheDocument();
    });

    it('should display minutes for recent articles', () => {
      const tenMinutesAgo = new Date(Date.now() - 10 * 60000);
      const recentArticle = {
        ...mockArticles[0],
        created_at: tenMinutesAgo.toISOString(),
      };

      mockUseApi.mockReturnValue({
        data: [recentArticle],
        loading: false,
        error: null,
      });

      render(<NewsFeed />);
      expect(screen.getByText('10m ago')).toBeInTheDocument();
    });

    it('should display hours for articles from today', () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60000);
      const article = {
        ...mockArticles[0],
        created_at: twoHoursAgo.toISOString(),
      };

      mockUseApi.mockReturnValue({
        data: [article],
        loading: false,
        error: null,
      });

      render(<NewsFeed />);
      expect(screen.getByText('2h ago')).toBeInTheDocument();
    });

    it('should display days for older articles', () => {
      const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60000);
      const article = {
        ...mockArticles[0],
        created_at: threeDaysAgo.toISOString(),
      };

      mockUseApi.mockReturnValue({
        data: [article],
        loading: false,
        error: null,
      });

      render(<NewsFeed />);
      expect(screen.getByText('3d ago')).toBeInTheDocument();
    });
  });

  describe('Sentiment Colors', () => {
    it('should apply correct color class for positive sentiment', () => {
      const { container } = render(<NewsFeed />);
      const sentimentBadges = container.querySelectorAll('[class*="positive"]');
      expect(sentimentBadges.length).toBeGreaterThan(0);
    });

    it('should display all sentiment labels', () => {
      render(<NewsFeed />);
      expect(screen.getByText('positive')).toBeInTheDocument();
      expect(screen.getByText('negative')).toBeInTheDocument();
    });
  });

  describe('Responsive Layout', () => {
    it('should have max height for scrollable container', () => {
      const { container } = render(<NewsFeed />);
      const feedContainer = container.querySelector('[role="feed"]');
      expect(feedContainer).toHaveClass('max-h-[600px]');
    });

    it('should have overflow auto for scrolling', () => {
      const { container } = render(<NewsFeed />);
      const feedContainer = container.querySelector('[role="feed"]');
      expect(feedContainer).toHaveClass('overflow-y-auto');
    });

    it('should have proper padding on articles', () => {
      const { container } = render(<NewsFeed />);
      const articles = container.querySelectorAll('[role="article"]');
      articles.forEach(article => {
        expect(article).toHaveClass('px-4', 'py-3');
      });
    });
  });
});
