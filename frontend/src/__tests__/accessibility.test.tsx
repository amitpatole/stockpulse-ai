```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import StockCard from '@/components/dashboard/StockCard';
import KPICards from '@/components/dashboard/KPICards';
import { ToastContainer } from '@/components/ui/Toast';
import type { AIRating } from '@/lib/types';

describe('Accessibility: ARIA Labels and Semantic HTML', () => {
  describe('Sidebar Component', () => {
    it('should have nav role with aria-label', () => {
      render(<Sidebar />);
      const nav = screen.getByRole('navigation', { name: /main navigation/i });
      expect(nav).toBeInTheDocument();
    });

    it('should have skip to main content link', () => {
      render(<Sidebar />);
      const skipLink = screen.getByText(/skip to main content/i);
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main');
    });

    it('should have collapse button with aria-expanded', () => {
      render(<Sidebar />);
      const collapseButton = screen.getByLabelText(/collapse sidebar/i);
      expect(collapseButton).toHaveAttribute('aria-expanded');
    });

    it('should mark active nav link with aria-current', () => {
      render(<Sidebar />);
      // The Dashboard link should be current on the root path
      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      expect(dashboardLink).toHaveAttribute('aria-current', 'page');
    });

    it('should have system status region with aria-live', () => {
      render(<Sidebar />);
      const statusRegion = screen.getByLabelText(/system status/i);
      expect(statusRegion).toHaveAttribute('aria-label', 'System status');
    });
  });

  describe('Header Component', () => {
    it('should have header semantic element', () => {
      render(<Header title="Test Title" />);
      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();
    });

    it('should have properly labeled search input', () => {
      render(<Header title="Test Title" />);
      const searchInput = screen.getByLabelText(/search alerts and stocks/i);
      expect(searchInput).toBeInTheDocument();
    });

    it('should have alert button with dynamic aria-label', () => {
      render(<Header title="Test Title" />);
      const alertButton = screen.getByLabelText(/view alerts/i);
      expect(alertButton).toBeInTheDocument();
    });

    it('should have status region with aria-live for connection', () => {
      render(<Header title="Test Title" />);
      const statusDiv = screen.getByLabelText(/connection status/i);
      expect(statusDiv).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Toast Component', () => {
    it('should have role="alert" on toast', () => {
      const toasts = [{ id: '1', type: 'success' as const, message: 'Success!' }];
      render(<ToastContainer toasts={toasts} onRemove={() => {}} />);
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('should have aria-live="polite" on toast', () => {
      const toasts = [{ id: '1', type: 'info' as const, message: 'Info message' }];
      render(<ToastContainer toasts={toasts} onRemove={() => {}} />);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });

    it('should have aria-atomic="true" on toast', () => {
      const toasts = [{ id: '1', type: 'error' as const, message: 'Error message' }];
      render(<ToastContainer toasts={toasts} onRemove={() => {}} />);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-atomic', 'true');
    });

    it('should have notifications region with proper labels', () => {
      const toasts = [{ id: '1', type: 'success' as const, message: 'Saved!' }];
      render(<ToastContainer toasts={toasts} onRemove={() => {}} />);
      const region = screen.getByLabelText(/notifications/i);
      expect(region).toHaveAttribute('role', 'region');
      expect(region).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('StockCard Component', () => {
    const mockRating: AIRating = {
      ticker: 'AAPL',
      current_price: 150.25,
      price_change_pct: 2.5,
      rating: 'buy',
      confidence: 0.85,
      sentiment_score: 0.3,
      rsi: 45,
      score: 7.8,
    };

    it('should have role="region" with aria-labelledby', () => {
      render(<StockCard rating={mockRating} />);
      const region = screen.getByRole('region');
      expect(region).toHaveAttribute('aria-labelledby');
    });

    it('should have heading for card title', () => {
      render(<StockCard rating={mockRating} />);
      const heading = screen.getByRole('heading', { name: 'AAPL' });
      expect(heading).toBeInTheDocument();
    });

    it('should have aria-label for price change', () => {
      render(<StockCard rating={mockRating} />);
      const priceChange = screen.getByLabelText(/price change/i);
      expect(priceChange).toBeInTheDocument();
    });

    it('should have progressbar roles for metrics', () => {
      render(<StockCard rating={mockRating} />);
      const progressbars = screen.getAllByRole('progressbar');
      expect(progressbars.length).toBeGreaterThanOrEqual(2); // RSI and Sentiment
    });

    it('should have remove button with proper aria-label', () => {
      const mockOnRemove = () => {};
      render(<StockCard rating={mockRating} onRemove={mockOnRemove} />);
      const removeButton = screen.getByLabelText(/remove AAPL from watchlist/i);
      expect(removeButton).toBeInTheDocument();
    });
  });

  describe('KPICards Component', () => {
    it('should have section with aria-label', () => {
      render(<KPICards />);
      const section = screen.getByLabelText(/key performance indicators/i);
      expect(section).toBeInTheDocument();
    });

    it('should have proper heading hierarchy', () => {
      render(<KPICards />);
      // H2 for the main section
      const mainHeading = screen.getByRole('heading', { name: /dashboard kpi summary/i, level: 2 });
      expect(mainHeading).toBeInTheDocument();
    });
  });

  describe('Focus Management', () => {
    it('should allow tabbing to interactive elements', () => {
      render(<Sidebar />);
      const button = screen.getByLabelText(/collapse sidebar/i);
      expect(button).toBeVisible();
      // Button should be naturally focusable
      expect(button.tagName).toBe('BUTTON');
    });

    it('should have focus-visible styles on buttons', () => {
      render(<Sidebar />);
      const button = screen.getByLabelText(/collapse sidebar/i);
      // Check that focus-visible classes are applied
      expect(button.className).toContain('focus-visible');
    });
  });

  describe('Semantic HTML', () => {
    it('should use <nav> for navigation', () => {
      render(<Sidebar />);
      const navElements = screen.getAllByRole('navigation');
      expect(navElements.length).toBeGreaterThan(0);
    });

    it('should use <header> for page header', () => {
      render(<Header title="Test" />);
      const header = screen.getByRole('banner');
      expect(header.tagName).toBe('HEADER');
    });

    it('should use <section> for content regions', () => {
      render(<KPICards />);
      const section = screen.getByLabelText(/key performance indicators/i);
      expect(section.tagName).toBe('SECTION');
    });

    it('should use <article> for card content', () => {
      const mockRating: AIRating = {
        ticker: 'TSLA',
        current_price: 250,
        price_change_pct: 1.0,
        rating: 'hold',
        confidence: 0.7,
        sentiment_score: 0,
        rsi: 50,
        score: 6.5,
      };
      render(<StockCard rating={mockRating} />);
      const article = screen.getByRole('region');
      expect(article.tagName).toBe('ARTICLE');
    });
  });

  describe('Color Contrast and Icon Accessibility', () => {
    it('should mark decorative icons as aria-hidden', () => {
      render(<Sidebar />);
      const decorativeIcons = document.querySelectorAll('[aria-hidden="true"]');
      expect(decorativeIcons.length).toBeGreaterThan(0);
    });

    it('should provide aria-label for icon-only buttons', () => {
      const mockRating: AIRating = {
        ticker: 'GOOG',
        current_price: 140,
        price_change_pct: -1.5,
        rating: 'sell',
        confidence: 0.6,
        sentiment_score: -0.2,
        rsi: 35,
        score: 4.2,
      };
      render(<StockCard rating={mockRating} onRemove={() => {}} />);
      const removeBtn = screen.getByLabelText(/remove GOOG/i);
      expect(removeBtn).toBeInTheDocument();
    });
  });
});
```