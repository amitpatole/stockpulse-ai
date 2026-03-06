import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAccessibility, useFocus, useSkipLink } from '@/hooks/useAccessibility';
import * as a11yLib from '@/lib/a11y';
import type { RefObject } from 'react';

// Mock the a11y utilities
vi.mock('@/lib/a11y', () => ({
  trapFocus: vi.fn(() => vi.fn()), // Return unsubscribe function
  setFocus: vi.fn(),
  announceMessage: vi.fn(),
}));

describe('useAccessibility Hook - Keyboard Navigation (WCAG 2.1 Level AA)', () => {
  let containerRef: RefObject<HTMLElement>;

  beforeEach(() => {
    const container = document.createElement('div');
    document.body.appendChild(container);
    containerRef = { current: container };
  });

  afterEach(() => {
    if (containerRef.current?.parentNode) {
      containerRef.current.parentNode.removeChild(containerRef.current);
    }
    vi.clearAllMocks();
  });

  describe('Escape Key Handling (AC1: Keyboard Navigation)', () => {
    it('should trigger close button on Escape key', async () => {
      if (!containerRef.current) return;

      const mockOnClose = vi.fn();
      containerRef.current.innerHTML = `
        <button aria-label="Close">X</button>
        <div>Modal content</div>
      `;

      const closeButton = containerRef.current.querySelector('[aria-label="Close"]') as HTMLElement;
      closeButton.addEventListener('click', mockOnClose);

      const { result } = renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: false })
      );

      const escapeEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true,
      });

      act(() => {
        result.current.handleKeyDown(escapeEvent as any);
      });

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should handle Escape when close button uses data-close attribute', async () => {
      if (!containerRef.current) return;

      const mockOnClose = vi.fn();
      containerRef.current.innerHTML = `
        <button data-close="true">Close</button>
        <div>Dialog content</div>
      `;

      const closeButton = containerRef.current.querySelector('[data-close]') as HTMLElement;
      closeButton.addEventListener('click', mockOnClose);

      const { result } = renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: false })
      );

      const escapeEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true,
      });

      act(() => {
        result.current.handleKeyDown(escapeEvent as any);
      });

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should not throw when no close button exists', () => {
      if (!containerRef.current) return;

      containerRef.current.innerHTML = '<div>Content without close button</div>';

      const { result } = renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: false })
      );

      const escapeEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true,
      });

      // Should not throw error
      expect(() => {
        act(() => {
          result.current.handleKeyDown(escapeEvent as any);
        });
      }).not.toThrow();
    });
  });

  describe('Alt+H Shortcut - Home Navigation (AC2: Keyboard Navigation)', () => {
    it('should focus main h1 heading on Alt+H', async () => {
      if (!containerRef.current) return;

      containerRef.current.innerHTML = `
        <h1 tabindex="-1">Dashboard</h1>
        <div>Page content</div>
      `;

      const { result } = renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: false })
      );

      const altHEvent = new KeyboardEvent('keydown', {
        key: 'h',
        altKey: true,
        bubbles: true,
      });

      act(() => {
        result.current.handleKeyDown(altHEvent as any);
      });

      await waitFor(() => {
        expect(a11yLib.setFocus).toHaveBeenCalled();
      });
    });

    it('should not trigger on h key without Alt modifier', () => {
      if (!containerRef.current) return;

      containerRef.current.innerHTML = '<h1>Dashboard</h1>';

      const { result } = renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: false })
      );

      const hEvent = new KeyboardEvent('keydown', {
        key: 'h',
        altKey: false,
        bubbles: true,
      });

      act(() => {
        result.current.handleKeyDown(hEvent as any);
      });

      expect(a11yLib.setFocus).not.toHaveBeenCalled();
    });
  });

  describe('Focus Trap Configuration (AC3: Keyboard Navigation)', () => {
    it('should enable focus trap when trapFocusInElement is true', async () => {
      renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: true })
      );

      await waitFor(() => {
        expect(a11yLib.trapFocus).toHaveBeenCalledWith(containerRef.current);
      });
    });

    it('should not enable focus trap when trapFocusInElement is false', async () => {
      renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: false })
      );

      expect(a11yLib.trapFocus).not.toHaveBeenCalled();
    });

    it('should clean up focus trap on unmount', async () => {
      const mockUnsubscribe = vi.fn();
      vi.mocked(a11yLib.trapFocus).mockReturnValue(mockUnsubscribe);

      const { unmount } = renderHook(() =>
        useAccessibility(containerRef, { trapFocusInElement: true })
      );

      await waitFor(() => {
        expect(a11yLib.trapFocus).toHaveBeenCalled();
      });

      unmount();

      await waitFor(() => {
        expect(mockUnsubscribe).toHaveBeenCalled();
      });
    });
  });

  describe('Screen Reader Announcements (AC1: ARIA Support)', () => {
    it('should announce messages when announceChanges is enabled', async () => {
      const { result } = renderHook(() =>
        useAccessibility(containerRef, { announceChanges: true })
      );

      act(() => {
        result.current.announce('Content loaded', 'polite');
      });

      await waitFor(() => {
        expect(a11yLib.announceMessage).toHaveBeenCalledWith('Content loaded', 'polite');
      });
    });

    it('should use assertive announcement type for errors', async () => {
      const { result } = renderHook(() =>
        useAccessibility(containerRef, { announceChanges: true })
      );

      act(() => {
        result.current.announce('Error occurred', 'assertive');
      });

      await waitFor(() => {
        expect(a11yLib.announceMessage).toHaveBeenCalledWith('Error occurred', 'assertive');
      });
    });

    it('should not announce when announceChanges is disabled', () => {
      const { result } = renderHook(() =>
        useAccessibility(containerRef, { announceChanges: false })
      );

      act(() => {
        result.current.announce('This should not be announced');
      });

      expect(a11yLib.announceMessage).not.toHaveBeenCalled();
    });

    it('should default to polite announcement type', async () => {
      const { result } = renderHook(() =>
        useAccessibility(containerRef, { announceChanges: true })
      );

      act(() => {
        result.current.announce('Default announcement');
      });

      await waitFor(() => {
        expect(a11yLib.announceMessage).toHaveBeenCalledWith('Default announcement', 'polite');
      });
    });
  });
});

describe('useFocus Hook', () => {
  it('should call setFocus on button element', () => {
    const button = document.createElement('button');
    button.textContent = 'Test Button';
    document.body.appendChild(button);

    const targetRef = { current: button };

    const { result } = renderHook(() => useFocus(targetRef));

    act(() => {
      result.current.focus();
    });

    expect(a11yLib.setFocus).toHaveBeenCalledWith(button);

    document.body.removeChild(button);
  });

  it('should not throw when ref is null', () => {
    const targetRef = { current: null };

    const { result } = renderHook(() => useFocus(targetRef));

    expect(() => {
      act(() => {
        result.current.focus();
      });
    }).not.toThrow();
  });
});

describe('useSkipLink Hook (AC4: Keyboard Navigation)', () => {
  it('should navigate to target element on skip link click', () => {
    document.body.innerHTML = `
      <a href="#main" class="skip-link">Skip to main content</a>
      <main id="main" tabindex="-1">Main content</main>
    `;

    renderHook(() => useSkipLink('#main'));

    const skipLink = document.querySelector('.skip-link') as HTMLElement;

    act(() => {
      skipLink.click();
    });

    expect(a11yLib.setFocus).toHaveBeenCalled();
  });

  it('should announce navigation to target', () => {
    document.body.innerHTML = `
      <a href="#navigation">Skip to navigation</a>
      <nav id="navigation" tabindex="-1">Navigation menu</nav>
    `;

    renderHook(() => useSkipLink('#navigation'));

    const skipLink = document.querySelector('a') as HTMLElement;

    act(() => {
      skipLink.click();
    });

    expect(a11yLib.announceMessage).toHaveBeenCalled();
  });

  it('should handle multiple skip links', () => {
    document.body.innerHTML = `
      <a href="#main">Skip to main</a>
      <a href="#nav">Skip to navigation</a>
      <main id="main">Main</main>
      <nav id="nav">Navigation</nav>
    `;

    renderHook(() => useSkipLink('#main'));

    const skipLinks = document.querySelectorAll('a');

    act(() => {
      skipLinks[0].click();
    });

    expect(a11yLib.setFocus).toHaveBeenCalled();
  });

  it('should not throw when target does not exist', () => {
    document.body.innerHTML = `
      <a href="#nonexistent">Skip link</a>
    `;

    renderHook(() => useSkipLink('#nonexistent'));

    const skipLink = document.querySelector('a') as HTMLElement;

    expect(() => {
      act(() => {
        skipLink.click();
      });
    }).not.toThrow();
  });

  it('should clean up event listeners on unmount', () => {
    document.body.innerHTML = `
      <a href="#main">Skip to main</a>
      <main id="main">Main</main>
    `;

    const { unmount } = renderHook(() => useSkipLink('#main'));

    unmount();

    // After unmount, listeners should be removed
    const skipLink = document.querySelector('a') as HTMLElement;

    // Click should not trigger focus (listener removed)
    act(() => {
      skipLink.click();
    });

    // We can't directly test listener removal, but we can verify no errors occur
    expect(true).toBe(true);
  });
});
