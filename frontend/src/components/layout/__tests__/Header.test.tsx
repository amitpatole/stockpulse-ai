import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Header from '../Header';
import { useSSE } from '@/hooks/useSSE';

// Mock the useSSE hook
vi.mock('@/hooks/useSSE', () => ({
  useSSE: vi.fn(),
}));

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Happy path: Renders title and subtitle with connection live
  it('should render title and subtitle with live connection status', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [],
    });

    render(<Header title="Dashboard" subtitle="Real-time alerts" />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Real-time alerts')).toBeInTheDocument();
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  // Edge case: No subtitle should not render subtitle element
  it('should render title only when subtitle is undefined', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [],
    });

    render(<Header title="Dashboard" />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.queryByRole('paragraph')).not.toBeInTheDocument();
  });

  // Business logic: Connection status styling based on SSE connection state
  it('should show offline status with red styling when connection lost', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: false,
      recentAlerts: [],
    });

    render(<Header title="Dashboard" />);

    const statusElement = screen.getByText('Offline');
    expect(statusElement).toBeInTheDocument();
    // Verify red styling
    expect(statusElement.closest('div')).toHaveClass('bg-red-500/10');
    expect(statusElement.closest('div')).toHaveClass('text-red-400');
  });

  // Business logic: Alert badge shows count of unread alerts
  it('should display badge with alert count when alerts present', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [
        { id: '1', ticker: 'AAPL', type: 'price_breach', triggered_at: new Date().toISOString() },
        { id: '2', ticker: 'GOOGL', type: 'price_breach', triggered_at: new Date().toISOString() },
      ],
    });

    render(<Header title="Dashboard" />);

    // Badge should show count
    expect(screen.getByText('2')).toBeInTheDocument();
    // Alert button should have accessible label with count
    expect(screen.getByLabelText('View alerts (2 unread)')).toBeInTheDocument();
  });

  // Edge case: No alerts should not render badge
  it('should not display alert badge when no alerts', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [],
    });

    render(<Header title="Dashboard" />);

    // Badge should not be present
    expect(screen.queryByText('0')).not.toBeInTheDocument();
    // Button label should show 0 unread
    expect(screen.getByLabelText('View alerts (0 unread)')).toBeInTheDocument();
  });

  // Business logic: Alert badge caps at 9+ for large numbers
  it('should display "9+" badge when more than 9 alerts', () => {
    const alerts = Array.from({ length: 12 }, (_, i) => ({
      id: String(i),
      ticker: 'AAPL',
      type: 'price_breach' as const,
      triggered_at: new Date().toISOString(),
    }));

    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: alerts,
    });

    render(<Header title="Dashboard" />);

    expect(screen.getByText('9+')).toBeInTheDocument();
    expect(screen.getByLabelText('View alerts (12 unread)')).toBeInTheDocument();
  });

  // UI: Search input should have proper placeholder and keyboard shortcut hint
  it('should render search input with keyboard shortcut indicator', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [],
    });

    render(<Header title="Dashboard" />);

    const searchInput = screen.getByPlaceholderText('Search...');
    expect(searchInput).toBeInTheDocument();
    expect(searchInput).toHaveAttribute('aria-label', 'Search alerts and stocks');

    // Keyboard shortcut should be visible
    expect(screen.getByText('/')).toBeInTheDocument();
  });

  // Accessibility: Connection status should be live region
  it('should have connection status as live region for announcements', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: false,
      recentAlerts: [],
    });

    render(<Header title="Dashboard" />);

    const statusDiv = screen.getByLabelText('Connection status: Offline');
    expect(statusDiv).toHaveAttribute('aria-live', 'polite');
  });

  // UI: Alert button has focus styling and can be interacted with
  it('should have accessible alert button with focus states', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [
        { id: '1', ticker: 'AAPL', type: 'price_breach', triggered_at: new Date().toISOString() },
      ],
    });

    render(<Header title="Dashboard" />);

    const alertButton = screen.getByLabelText('View alerts (1 unread)');
    expect(alertButton).toHaveClass('focus:ring-2');
    expect(alertButton).toHaveClass('focus:ring-blue-500');
  });

  // Edge case: Rendered title can be any string (special characters, long text)
  it('should render titles with special characters and long text', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [],
    });

    render(
      <Header
        title="Market Analysis & Trading 📊"
        subtitle="Real-time data as of 3:45 PM EST"
      />
    );

    expect(screen.getByText('Market Analysis & Trading 📊')).toBeInTheDocument();
    expect(screen.getByText('Real-time data as of 3:45 PM EST')).toBeInTheDocument();
  });

  // UI: Icons should have aria-hidden for decorative purposes
  it('should have decorative icons properly hidden from accessibility tree', () => {
    (useSSE as ReturnType<typeof vi.fn>).mockReturnValue({
      connected: true,
      recentAlerts: [],
    });

    const { container } = render(<Header title="Dashboard" />);

    // All lucide SVG icons should have aria-hidden
    const svgIcons = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(svgIcons.length).toBeGreaterThan(0);
    svgIcons.forEach((icon) => {
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });
  });
});
