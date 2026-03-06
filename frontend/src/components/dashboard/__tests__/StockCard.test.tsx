import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StockCard from '../StockCard';
import { mockData } from '@/__tests__/setup';

describe('StockCard', () => {
  // Happy path: Renders all metrics correctly with valid data
  it('should render stock ticker, price, and all metrics', () => {
    const rating = mockData.rating({
      ticker: 'AAPL',
      current_price: 150.25,
      price_change_pct: 2.5,
      rating: 'buy',
      confidence: 0.85,
      sentiment_score: 0.45,
      rsi: 55,
      score: 7.5,
    });

    render(<StockCard rating={rating} />);

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('$150.25')).toBeInTheDocument();
    expect(screen.getByText('+2.50%')).toBeInTheDocument();
    expect(screen.getByText(/buy/i)).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument(); // confidence
    expect(screen.getByText('55.0')).toBeInTheDocument(); // RSI
    expect(screen.getByText('+0.45')).toBeInTheDocument(); // sentiment
    expect(screen.getByText('7.5/10')).toBeInTheDocument(); // AI score
  });

  // Edge case: Negative price change displays correctly with red styling
  it('should format negative price change with minus sign and red styling', () => {
    const rating = mockData.rating({
      ticker: 'GOOGL',
      price_change_pct: -1.23,
    });

    render(<StockCard rating={rating} />);

    const changeElement = screen.getByText('-1.23%');
    expect(changeElement).toBeInTheDocument();
    // Verify red styling is applied
    expect(changeElement.closest('div')).toHaveClass('bg-red-500/10');
  });

  // Edge case: Zero price change displays without sign, neutral color
  it('should display zero price change without sign in neutral color', () => {
    const rating = mockData.rating({
      price_change_pct: 0,
    });

    render(<StockCard rating={rating} />);

    const changeElement = screen.getByText('0.00%');
    expect(changeElement).toBeInTheDocument();
    expect(changeElement.closest('div')).toHaveClass('bg-slate-500/10');
  });

  // Business logic: RSI color-coding thresholds (>70 red, <30 green, else blue)
  it('should color-code RSI based on overbought/oversold thresholds', () => {
    const { rerender } = render(
      <StockCard rating={mockData.rating({ rsi: 75 })} />
    );
    // Overbought (>70) should be red
    expect(screen.getByText('75.0').closest('span')).toHaveClass('text-red-400');

    rerender(<StockCard rating={mockData.rating({ rsi: 25 })} />);
    // Oversold (<30) should be green
    expect(screen.getByText('25.0').closest('span')).toHaveClass(
      'text-emerald-400'
    );

    rerender(<StockCard rating={mockData.rating({ rsi: 50 })} />);
    // Normal (30-70) should be gray
    expect(screen.getByText('50.0').closest('span')).toHaveClass(
      'text-slate-300'
    );
  });

  // Business logic: Sentiment color-coding (>0.2 positive, <-0.2 negative, else neutral)
  it('should color-code sentiment score based on thresholds', () => {
    const { rerender } = render(
      <StockCard rating={mockData.rating({ sentiment_score: 0.5 })} />
    );
    // Positive (>0.2)
    expect(screen.getByText('+0.50').closest('span')).toHaveClass(
      'text-emerald-400'
    );

    rerender(<StockCard rating={mockData.rating({ sentiment_score: -0.5 })} />);
    // Negative (<-0.2)
    expect(screen.getByText('-0.50').closest('span')).toHaveClass(
      'text-red-400'
    );

    rerender(<StockCard rating={mockData.rating({ sentiment_score: 0.1 })} />);
    // Neutral (-0.2 to 0.2)
    expect(screen.getByText('+0.10').closest('span')).toHaveClass(
      'text-slate-300'
    );
  });

  // Edge case: Missing score field should not render score section
  it('should not render AI score section if score is null', () => {
    const rating = mockData.rating({ score: undefined });
    render(<StockCard rating={rating} />);

    expect(screen.queryByText(/10$/)).not.toBeInTheDocument(); // "X/10" pattern
  });

  // User interaction: Remove button triggers callback with correct ticker
  it('should call onRemove with ticker when remove button clicked', async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn();
    const rating = mockData.rating({ ticker: 'MSFT' });

    render(<StockCard rating={rating} onRemove={onRemove} />);

    const removeButton = screen.getByLabelText('Remove MSFT from watchlist');
    await user.click(removeButton);

    expect(onRemove).toHaveBeenCalledWith('MSFT');
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  // UI behavior: Remove button hidden by default, shows on hover/focus
  it('should render remove button with hidden opacity until hover/focus', () => {
    const onRemove = vi.fn();
    const rating = mockData.rating();

    render(<StockCard rating={rating} onRemove={onRemove} />);

    const removeButton = screen.getByLabelText(/Remove/);
    // Button should have group-hover:opacity-100 and focus:opacity-100 classes
    expect(removeButton).toHaveClass('opacity-0');
    expect(removeButton).toHaveClass('group-hover:opacity-100');
  });

  // Edge case: Missing optional fields display fallback values
  it('should display fallback values for missing optional fields', () => {
    const rating = {
      ticker: 'TEST',
      rating: undefined,
      current_price: undefined,
      price_change_pct: undefined,
      confidence: undefined,
      rsi: undefined,
      sentiment_score: undefined,
      score: undefined,
    } as any;

    render(<StockCard rating={rating} />);

    expect(screen.getByText('—')).toBeInTheDocument(); // fallback for price
    expect(screen.getByText('0.00%')).toBeInTheDocument(); // default for change %
    expect(screen.getByText('N/A')).toBeInTheDocument(); // fallback for rating
  });

  // Accessibility: Aria labels and progress bar ARIA attributes
  it('should have proper accessibility attributes for metrics', () => {
    const rating = mockData.rating({
      rsi: 65,
      sentiment_score: 0.3,
    });

    render(<StockCard rating={rating} />);

    // RSI progress bar
    const rsiBar = screen.getByLabelText('RSI: 65.0');
    expect(rsiBar).toHaveAttribute('role', 'progressbar');
    expect(rsiBar).toHaveAttribute('aria-valuenow', '65');
    expect(rsiBar).toHaveAttribute('aria-valuemin', '0');
    expect(rsiBar).toHaveAttribute('aria-valuemax', '100');

    // Sentiment progress bar
    const sentimentBar = screen.getByLabelText('Sentiment: +0.30');
    expect(sentimentBar).toHaveAttribute('role', 'progressbar');
  });

  // Edge case: Rating format (underscores replaced with spaces)
  it('should format rating labels by replacing underscores with spaces', () => {
    const rating = mockData.rating({ rating: 'strong_buy' });
    render(<StockCard rating={rating} />);

    expect(screen.getByText('strong buy')).toBeInTheDocument();
  });

  // Business logic: Sentiment percentage calculation from -1 to 1 range to 0-100
  it('should convert sentiment score from -1 to 1 range to 0-100 percentage for progress bar', () => {
    // Sentiment -1 should map to 0%, +1 should map to 100%, 0 should map to 50%
    const { rerender } = render(
      <StockCard rating={mockData.rating({ sentiment_score: -1 })} />
    );
    const sentimentBar = screen.getByLabelText(/Sentiment/);
    expect(sentimentBar).toHaveAttribute('aria-valuenow', '0');

    rerender(<StockCard rating={mockData.rating({ sentiment_score: 1 })} />);
    expect(screen.getByLabelText(/Sentiment/)).toHaveAttribute(
      'aria-valuenow',
      '100'
    );

    rerender(<StockCard rating={mockData.rating({ sentiment_score: 0 })} />);
    expect(screen.getByLabelText(/Sentiment/)).toHaveAttribute('aria-valuenow', '50');
  });
});
