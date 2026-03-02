```typescript
import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuotaCard } from '@/components/QuotaCard';

describe('QuotaCard Component', () => {
  const mockQuota = {
    provider: 'sec',
    quota_type: 'bulk_submissions',
    limit: 100,
    used: 42,
    percent_used: 42,
    reset_at: '2026-03-03T00:00:00Z',
    status: 'normal' as const,
    last_updated: '2026-03-02T10:30:00Z',
  };

  it('renders provider name and quota type', () => {
    render(<QuotaCard quota={mockQuota} />);
    expect(screen.getByText('Sec')).toBeInTheDocument();
    expect(screen.getByText('Bulk Submissions')).toBeInTheDocument();
  });

  it('displays correct usage and limit', () => {
    render(<QuotaCard quota={mockQuota} />);
    expect(screen.getByText(/42 \/ 100/)).toBeInTheDocument();
    expect(screen.getByText('42%')).toBeInTheDocument();
  });

  it('shows status badge', () => {
    render(<QuotaCard quota={mockQuota} />);
    expect(screen.getByText('Normal')).toBeInTheDocument();
  });

  it('displays reset time when available', () => {
    render(<QuotaCard quota={mockQuota} />);
    expect(screen.getByText(/Resets:/)).toBeInTheDocument();
  });

  it('applies correct color classes for normal status', () => {
    const { container } = render(<QuotaCard quota={mockQuota} />);
    const cardElement = container.querySelector('[data-testid="quota-card"]');
    expect(cardElement).toHaveClass('bg-green-50');
    expect(cardElement).toHaveClass('border-green-200');
  });

  it('applies correct color classes for warning status', () => {
    const warningQuota = { ...mockQuota, status: 'warning' as const, percent_used: 65 };
    const { container } = render(<QuotaCard quota={warningQuota} />);
    const cardElement = container.querySelector('[data-testid="quota-card"]');
    expect(cardElement).toHaveClass('bg-yellow-50');
    expect(cardElement).toHaveClass('border-yellow-200');
  });

  it('applies correct color classes for critical status', () => {
    const criticalQuota = { ...mockQuota, status: 'critical' as const, percent_used: 95 };
    const { container } = render(<QuotaCard quota={criticalQuota} />);
    const cardElement = container.querySelector('[data-testid="quota-card"]');
    expect(cardElement).toHaveClass('bg-red-50');
    expect(cardElement).toHaveClass('border-red-200');
  });

  it('renders progress bar at correct width', () => {
    render(<QuotaCard quota={mockQuota} />);
    const progressBar = screen.getByRole('button', { hidden: true })?.parentElement?.querySelector('.bg-green-500');
    // The progress bar exists in the component
    const { container } = render(<QuotaCard quota={mockQuota} />);
    const bar = container.querySelector('.bg-green-500');
    expect(bar).toHaveStyle(`width: 42%`);
  });

  it('handles zero limit gracefully', () => {
    const zeroLimitQuota = { ...mockQuota, limit: 0, percent_used: 0 };
    render(<QuotaCard quota={zeroLimitQuota} />);
    expect(screen.getByText(/0 \/ 0/)).toBeInTheDocument();
  });

  it('handles very large numbers with localeString', () => {
    const largeQuota = {
      ...mockQuota,
      limit: 1000000,
      used: 500000,
    };
    render(<QuotaCard quota={largeQuota} />);
    expect(screen.getByText(/500,000 \/ 1,000,000/)).toBeInTheDocument();
  });

  it('shows no reset time message when reset_at is null', () => {
    const noResetQuota = { ...mockQuota, reset_at: null };
    render(<QuotaCard quota={noResetQuota} />);
    expect(screen.getByText('No reset time specified')).toBeInTheDocument();
  });

  it('handles invalid reset time gracefully', () => {
    const invalidQuota = { ...mockQuota, reset_at: 'invalid-date' };
    render(<QuotaCard quota={invalidQuota} />);
    expect(screen.getByText(/Resets:/)).toBeInTheDocument();
  });
});
```