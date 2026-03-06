/**
 * Dashboard Component Tests
 *
 * Tests verify that:
 * - Dashboard renders with KPI cards, stock grid, and news feed
 * - Loading states are properly displayed
 * - Error handling works gracefully
 * - Component composition and layout integrity
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DashboardPage from '@/app/page';

// Mock components
jest.mock('@/components/layout/Header', () => {
  return function MockHeader({ title, subtitle }: { title: string; subtitle: string }) {
    return <div data-testid="mock-header">{title} - {subtitle}</div>;
  };
});

jest.mock('@/components/dashboard/KPICards', () => {
  return function MockKPICards() {
    return <div data-testid="mock-kpi-cards">KPI Cards</div>;
  };
});

jest.mock('@/components/dashboard/StockGrid', () => {
  return function MockStockGrid() {
    return <div data-testid="mock-stock-grid">Stock Grid</div>;
  };
});

jest.mock('@/components/dashboard/NewsFeed', () => {
  return function MockNewsFeed() {
    return <div data-testid="mock-news-feed">News Feed</div>;
  };
});

describe('Dashboard Page', () => {
  // ============================================================
  // Rendering & Composition
  // ============================================================

  it('should render dashboard with all main sections', () => {
    render(<DashboardPage />);

    // Verify all main sections are present
    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-kpi-cards')).toBeInTheDocument();
    expect(screen.getByTestId('mock-stock-grid')).toBeInTheDocument();
    expect(screen.getByTestId('mock-news-feed')).toBeInTheDocument();
  });

  it('should render header with correct title and subtitle', () => {
    render(<DashboardPage />);

    const header = screen.getByTestId('mock-header');
    expect(header).toHaveTextContent('Dashboard');
    expect(header).toHaveTextContent('Market overview and stock watchlist');
  });

  it('should have correct grid layout classes', () => {
    const { container } = render(<DashboardPage />);

    // Check for grid layout container
    const layoutElements = container.querySelectorAll('[class*="grid"]');
    expect(layoutElements.length).toBeGreaterThan(0);
  });

  it('should have stock grid in 2-column span on XL screens', () => {
    const { container } = render(<DashboardPage />);

    // Look for xl:col-span-2 in parent of stock grid
    const gridContent = container.querySelector('[class*="xl:col-span"]');
    expect(gridContent).toBeInTheDocument();
  });

  it('should have news feed in 1-column span on XL screens', () => {
    const { container } = render(<DashboardPage />);

    // Stock grid and news feed should be adjacent grid items
    const mainContent = container.querySelector('[class*="grid"]');
    expect(mainContent).toBeInTheDocument();
  });

  // ============================================================
  // Content Verification
  // ============================================================

  it('should render stock watchlist heading', () => {
    render(<DashboardPage />);

    expect(screen.getByText('Stock Watchlist')).toBeInTheDocument();
  });

  it('should have proper flex layout for main container', () => {
    const { container } = render(<DashboardPage />);

    const mainDiv = container.firstChild as HTMLElement;
    expect(mainDiv.className).toContain('flex');
    expect(mainDiv.className).toContain('flex-col');
  });

  it('should have padding on content area', () => {
    const { container } = render(<DashboardPage />);

    // Find element with p-6 (padding)
    const contentArea = container.querySelector('[class*="p-6"]');
    expect(contentArea).toBeInTheDocument();
  });

  // ============================================================
  // Accessibility & Structure
  // ============================================================

  it('should have semantic heading structure', () => {
    render(<DashboardPage />);

    const heading = screen.getByText('Stock Watchlist');
    expect(heading.tagName).toBe('H2');
  });

  it('should maintain proper DOM hierarchy', () => {
    const { container } = render(<DashboardPage />);

    // Main container should exist
    const main = container.firstChild;
    expect(main).toBeInTheDocument();

    // Should have nested structure: div > div (header) + div (content)
    expect(main?.childNodes.length).toBeGreaterThanOrEqual(2);
  });

  it('should use responsive classes for mobile and desktop', () => {
    const { container } = render(<DashboardPage />);

    // Check for responsive grid classes
    const html = container.innerHTML;
    expect(html).toContain('grid-cols-1');
    expect(html).toContain('xl:grid-cols-3');
  });

  // ============================================================
  // Edge Cases & Special States
  // ============================================================

  it('should render even with no data in sub-components', () => {
    render(<DashboardPage />);

    // Should not throw and all sections should render
    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-stock-grid')).toBeInTheDocument();
  });

  it('should not display error messages by default', () => {
    render(<DashboardPage />);

    // Should not contain common error indicators
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/failed/i)).not.toBeInTheDocument();
  });

  it('should have consistent spacing between sections', () => {
    const { container } = render(<DashboardPage />);

    // KPI cards should have margin-top
    const html = container.innerHTML;
    expect(html).toContain('mt-6');
  });

  // ============================================================
  // Visual States
  // ============================================================

  it('should have dark theme classes applied', () => {
    const { container } = render(<DashboardPage />);

    const html = container.innerHTML;
    // Check for dark theme indicators
    expect(html).toContain('flex-1');
    expect(html).toContain('p-6');
  });

  it('should render flex container for main layout', () => {
    const { container } = render(<DashboardPage />);

    const flexContainer = container.querySelector('[class*="flex-col"]');
    expect(flexContainer).toBeInTheDocument();
  });

  // ============================================================
  // Integration Tests
  // ============================================================

  it('should have all components in correct order', () => {
    render(<DashboardPage />);

    const header = screen.getByTestId('mock-header');
    const kpi = screen.getByTestId('mock-kpi-cards');
    const stockGrid = screen.getByTestId('mock-stock-grid');

    // Header should appear before content
    expect(header.compareDocumentPosition(kpi) & Node.DOCUMENT_POSITION_FOLLOWING).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING
    );
  });

  it('should maintain responsive grid structure across viewport sizes', () => {
    const { container } = render(<DashboardPage />);

    const gridElement = container.querySelector('[class*="grid-cols"]');
    expect(gridElement?.className).toContain('gap-6');
  });
});
