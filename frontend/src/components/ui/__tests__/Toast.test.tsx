/**
 * Toast Component Tests
 *
 * Tests for Toast notification component and useToast hook.
 * Covers both single Toast rendering and ToastContainer management.
 *
 * Coverage:
 * - Toast rendering with different types (success, error, info)
 * - Auto-dismiss on timer expiration
 * - Manual close with button click
 * - useToast hook state management
 * - Accessibility (ARIA labels, alerts)
 * - Edge cases (zero duration, rapid actions)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Toast, ToastContainer, useToast } from '../Toast';

/**
 * AC1: Toast displays type-specific icon and message
 * AC2: Auto-dismiss on timer (default 3000ms)
 * AC3: Manual close with button preserves other toasts
 * AC4: useToast hook manages toast state (add, remove, success, error, info)
 */

describe('Toast Component', () => {
  /**
   * HAPPY PATH: Render success toast with icon and message
   */
  it('should render success toast with correct styling and icon', () => {
    const onClose = vi.fn();

    render(
      <Toast
        id="toast-1"
        type="success"
        message="Settings saved successfully"
        onClose={onClose}
      />
    );

    // Message visible
    expect(screen.getByText('Settings saved successfully')).toBeInTheDocument();

    // Close button has proper aria-label
    const closeButton = screen.getByRole('button', {
      name: /close success notification/i,
    });
    expect(closeButton).toBeInTheDocument();

    // Toast has alert role for accessibility
    const toast = screen.getByRole('alert');
    expect(toast).toHaveAttribute('aria-live', 'polite');
    expect(toast).toHaveAttribute('aria-atomic', 'true');
  });

  /**
   * HAPPY PATH: Render error and info toasts
   */
  it('should render error and info toasts with correct styling', () => {
    const onClose = vi.fn();

    const { rerender } = render(
      <Toast id="toast-2" type="error" message="Operation failed" onClose={onClose} />
    );

    expect(screen.getByText('Operation failed')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /close error notification/i })
    ).toBeInTheDocument();

    rerender(
      <Toast id="toast-3" type="info" message="Please review" onClose={onClose} />
    );

    expect(screen.getByText('Please review')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /close information notification/i })
    ).toBeInTheDocument();
  });

  /**
   * HAPPY PATH: Auto-dismiss after default duration
   */
  it('should auto-dismiss toast after 3000ms (default)', async () => {
    vi.useFakeTimers();
    const onClose = vi.fn();

    render(
      <Toast
        id="toast-auto"
        type="success"
        message="Auto-dismiss test"
        onClose={onClose}
        duration={3000}
      />
    );

    expect(onClose).not.toHaveBeenCalled();

    // Fast-forward 3000ms
    vi.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledWith('toast-auto');
    });

    vi.useRealTimers();
  });

  /**
   * HAPPY PATH: Manual close via button click
   */
  it('should close toast when close button is clicked', async () => {
    const onClose = vi.fn();

    render(
      <Toast
        id="toast-manual"
        type="success"
        message="Click to close"
        onClose={onClose}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close success/i });
    await userEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledWith('toast-manual');
  });

  /**
   * EDGE CASE: Duration of 0 means no auto-dismiss
   */
  it('should not auto-dismiss when duration is 0', async () => {
    vi.useFakeTimers();
    const onClose = vi.fn();

    render(
      <Toast
        id="toast-persistent"
        type="info"
        message="Persistent notification"
        duration={0}
        onClose={onClose}
      />
    );

    // Fast-forward way past default timeout
    vi.advanceTimersByTime(10000);

    expect(onClose).not.toHaveBeenCalled();

    // Must close manually
    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledWith('toast-persistent');

    vi.useRealTimers();
  });

  /**
   * EDGE CASE: Cleanup timer on unmount
   */
  it('should clear timeout on unmount', () => {
    vi.useFakeTimers();
    const onClose = vi.fn();

    const { unmount } = render(
      <Toast
        id="toast-cleanup"
        type="success"
        message="Test cleanup"
        duration={3000}
        onClose={onClose}
      />
    );

    unmount();

    // Advance timer past when it would have fired
    vi.advanceTimersByTime(5000);

    // onClose should not be called after unmount
    expect(onClose).not.toHaveBeenCalled();

    vi.useRealTimers();
  });
});

describe('ToastContainer Component', () => {
  /**
   * HAPPY PATH: Render multiple toasts
   */
  it('should render multiple toasts in container', () => {
    const onRemove = vi.fn();

    const toasts = [
      { id: '1', type: 'success' as const, message: 'First toast' },
      { id: '2', type: 'error' as const, message: 'Second toast' },
      { id: '3', type: 'info' as const, message: 'Third toast' },
    ];

    render(<ToastContainer toasts={toasts} onRemove={onRemove} />);

    expect(screen.getByText('First toast')).toBeInTheDocument();
    expect(screen.getByText('Second toast')).toBeInTheDocument();
    expect(screen.getByText('Third toast')).toBeInTheDocument();

    // Container has proper accessibility
    const container = screen.getByRole('region', { name: /Notifications/i });
    expect(container).toHaveAttribute('aria-live', 'polite');
    expect(container).toHaveAttribute('aria-atomic', 'false');
  });

  /**
   * HAPPY PATH: Remove individual toast
   */
  it('should remove toast when onRemove is called', async () => {
    const onRemove = vi.fn();
    const toasts = [
      { id: '1', type: 'success' as const, message: 'Toast 1' },
      { id: '2', type: 'error' as const, message: 'Toast 2' },
    ];

    render(<ToastContainer toasts={toasts} onRemove={onRemove} />);

    const closeButtons = screen.getAllByRole('button');
    await userEvent.click(closeButtons[0]);

    expect(onRemove).toHaveBeenCalledWith('1');
  });

  /**
   * EDGE CASE: Render empty container
   */
  it('should render empty container when no toasts', () => {
    const onRemove = vi.fn();

    render(<ToastContainer toasts={[]} onRemove={onRemove} />);

    // Container exists but no toast messages
    const container = screen.getByRole('region', { name: /Notifications/i });
    expect(container).toBeEmptyDOMElement();
  });
});

describe('useToast Hook', () => {
  /**
   * HAPPY PATH: Hook manages toast state
   */
  it('should add and remove toasts via hook', async () => {
    function TestComponent() {
      const { toasts, addToast, removeToast } = useToast();

      return (
        <>
          <button onClick={() => addToast('Test message', 'success')}>
            Add Toast
          </button>
          {toasts.map((t) => (
            <div key={t.id}>
              <span>{t.message}</span>
              <button onClick={() => removeToast(t.id)}>Close</button>
            </div>
          ))}
        </>
      );
    }

    render(<TestComponent />);

    // No toasts initially
    expect(screen.queryByText('Test message')).not.toBeInTheDocument();

    // Add toast
    const addButton = screen.getByRole('button', { name: 'Add Toast' });
    await userEvent.click(addButton);

    expect(screen.getByText('Test message')).toBeInTheDocument();

    // Remove toast
    const closeButton = screen.getByRole('button', { name: 'Close' });
    await userEvent.click(closeButton);

    expect(screen.queryByText('Test message')).not.toBeInTheDocument();
  });

  /**
   * HAPPY PATH: Convenience methods (success, error, info)
   */
  it('should provide convenience methods for different toast types', async () => {
    function TestComponent() {
      const { toasts, success, error, info } = useToast();

      return (
        <>
          <button onClick={() => success('Success!')}>Success Button</button>
          <button onClick={() => error('Error!')}>Error Button</button>
          <button onClick={() => info('Info!')}>Info Button</button>
          {toasts.map((t) => (
            <div key={t.id} data-type={t.type}>
              {t.message}
            </div>
          ))}
        </>
      );
    }

    render(<TestComponent />);

    await userEvent.click(screen.getByRole('button', { name: 'Success Button' }));
    expect(screen.getByText('Success!').closest('div')).toHaveAttribute(
      'data-type',
      'success'
    );

    await userEvent.click(screen.getByRole('button', { name: 'Error Button' }));
    expect(screen.getByText('Error!').closest('div')).toHaveAttribute(
      'data-type',
      'error'
    );

    await userEvent.click(screen.getByRole('button', { name: 'Info Button' }));
    expect(screen.getByText('Info!').closest('div')).toHaveAttribute(
      'data-type',
      'info'
    );
  });

  /**
   * EDGE CASE: Multiple toasts with same message
   */
  it('should allow multiple toasts with same message (unique IDs)', async () => {
    function TestComponent() {
      const { toasts, addToast } = useToast();

      return (
        <>
          <button onClick={() => addToast('Same message', 'info')}>Add</button>
          <div data-testid="toast-count">{toasts.length}</div>
        </>
      );
    }

    render(<TestComponent />);

    const addButton = screen.getByRole('button', { name: 'Add' });
    await userEvent.click(addButton);
    await userEvent.click(addButton);
    await userEvent.click(addButton);

    expect(screen.getByTestId('toast-count')).toHaveTextContent('3');
  });
});
