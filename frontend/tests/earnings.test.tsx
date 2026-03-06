/**
 * Tests for Earnings Calendar components
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EarningsFilters } from '@/components/earnings/EarningsFilters';
import { EarningsTable } from '@/components/earnings/EarningsTable';
import { EarningsDetail } from '@/components/earnings/EarningsDetail';
import { calculateEPSSurprise, getEPSStatus, formatEarningsDate } from '@/lib/api/earnings';
import type { EarningsRecord } from '@/types/earnings';

describe('Earnings Calendar Components', () => {
  describe('calculateEPSSurprise', () => {
    it('calculates positive surprise', () => {
      const result = calculateEPSSurprise(1.00, 1.10);
      expect(result).toBeCloseTo(10.0, 1);
    });

    it('calculates negative surprise', () => {
      const result = calculateEPSSurprise(1.00, 0.90);
      expect(result).toBeCloseTo(-10.0, 1);
    });

    it('returns null for missing estimated', () => {
      expect(calculateEPSSurprise(null, 1.10)).toBeNull();
    });

    it('returns null for missing actual', () => {
      expect(calculateEPSSurprise(1.00, null)).toBeNull();
    });

    it('returns null for zero estimated', () => {
      expect(calculateEPSSurprise(0, 1.10)).toBeNull();
    });
  });

  describe('getEPSStatus', () => {
    it('returns beat for positive surprise > 0.5%', () => {
      expect(getEPSStatus(1.0)).toBe('beat');
    });

    it('returns miss for negative surprise < -0.5%', () => {
      expect(getEPSStatus(-1.0)).toBe('miss');
    });

    it('returns neutral for small surprise', () => {
      expect(getEPSStatus(0.0)).toBe('neutral');
    });

    it('returns null for null surprise', () => {
      expect(getEPSStatus(null)).toBeNull();
    });
  });

  describe('formatEarningsDate', () => {
    it('returns Today for current date', () => {
      const today = new Date('2026-03-06');
      const result = formatEarningsDate('2026-03-06', today);
      expect(result).toBe('Today');
    });

    it('returns days until for near future', () => {
      const today = new Date('2026-03-06');
      const result = formatEarningsDate('2026-03-10', today);
      expect(result).toContain('In');
      expect(result).toContain('days');
    });

    it('formats distant dates', () => {
      const today = new Date('2026-03-06');
      const result = formatEarningsDate('2026-06-30', today);
      expect(result).toContain('Jun');
      expect(result).toContain('30');
    });
  });

  describe('EarningsFilters', () => {
    it('renders filter controls', () => {
      const mockCallback = vi.fn();
      render(<EarningsFilters onFiltersChange={mockCallback} />);

      expect(screen.getByLabelText(/Status/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Start Date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/End Date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Ticker/i)).toBeInTheDocument();
    });

    it('calls callback on Apply Filters click', async () => {
      const user = userEvent.setup();
      const mockCallback = vi.fn();
      render(<EarningsFilters onFiltersChange={mockCallback} />);

      const applyButton = screen.getByText('Apply Filters');
      await user.click(applyButton);

      expect(mockCallback).toHaveBeenCalled();
    });

    it('resets filters on Reset click', async () => {
      const user = userEvent.setup();
      const mockCallback = vi.fn();
      render(<EarningsFilters onFiltersChange={mockCallback} />);

      const resetButton = screen.getByText('Reset');
      await user.click(resetButton);

      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          limit: 25,
          offset: 0,
        })
      );
    });
  });

  describe('EarningsTable', () => {
    const mockEarnings: EarningsRecord[] = [
      {
        id: 1,
        ticker: 'AAPL',
        earnings_date: '2026-04-28',
        estimated_eps: 1.82,
        actual_eps: 1.95,
        estimated_revenue: 91.5,
        actual_revenue: 93.7,
        surprise_percent: 7.14,
        fiscal_quarter: 'Q2',
        fiscal_year: 2026,
        status: 'reported',
      },
    ];

    it('renders earnings table', () => {
      render(<EarningsTable earnings={mockEarnings} />);

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('1.82')).toBeInTheDocument();
      expect(screen.getByText('1.95')).toBeInTheDocument();
    });

    it('shows empty message when no earnings', () => {
      render(<EarningsTable earnings={[]} />);

      expect(screen.getByText(/No earnings found/i)).toBeInTheDocument();
    });

    it('calls callback on row click', async () => {
      const user = userEvent.setup();
      const mockCallback = vi.fn();
      render(
        <EarningsTable earnings={mockEarnings} onEarningClick={mockCallback} />
      );

      const rows = screen.getAllByRole('row');
      await user.click(rows[1]); // Skip header row

      expect(mockCallback).toHaveBeenCalled();
    });
  });

  describe('EarningsDetail', () => {
    const mockEarning: EarningsRecord = {
      id: 1,
      ticker: 'AAPL',
      earnings_date: '2026-04-28',
      estimated_eps: 1.82,
      actual_eps: 1.95,
      estimated_revenue: 91.5,
      actual_revenue: 93.7,
      surprise_percent: 7.14,
      fiscal_quarter: 'Q2',
      fiscal_year: 2026,
      status: 'reported',
    };

    it('renders modal when open', () => {
      render(
        <EarningsDetail
          earning={mockEarning}
          isOpen={true}
          onClose={vi.fn()}
        />
      );

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('7.14% Surprise')).toBeInTheDocument();
    });

    it('closes on backdrop click', async () => {
      const user = userEvent.setup();
      const mockOnClose = vi.fn();
      const { container } = render(
        <EarningsDetail
          earning={mockEarning}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const backdrop = container.querySelector('[class*="fixed inset-0 bg-black"]');
      if (backdrop) {
        await user.click(backdrop);
        expect(mockOnClose).toHaveBeenCalled();
      }
    });

    it('does not render when isOpen is false', () => {
      const { container } = render(
        <EarningsDetail
          earning={mockEarning}
          isOpen={false}
          onClose={vi.fn()}
        />
      );

      expect(container.firstChild).toBeEmptyDOMElement();
    });
  });
});