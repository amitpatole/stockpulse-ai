/**
 * Accessibility utilities for WCAG 2.1 Level AA compliance
 * Focus management, keyboard event handling, and screen reader support
 */

/**
 * Get all focusable elements within a container
 * Includes buttons, links, inputs, and elements with tabindex
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const selector = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(',');

  return Array.from(container.querySelectorAll(selector)).filter((el) => {
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  });
}

/**
 * Set focus on an element and scroll it into view
 * Useful for managing focus after dynamic content changes
 */
export function setFocus(element: HTMLElement | null): void {
  if (!element) return;
  element.focus();
  element.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Get the first focusable element within a container
 * Useful for focus trapping in modals
 */
export function getFirstFocusable(container: HTMLElement): HTMLElement | null {
  const focusables = getFocusableElements(container);
  return focusables.length > 0 ? focusables[0] : null;
}

/**
 * Get the last focusable element within a container
 * Useful for focus trapping in modals
 */
export function getLastFocusable(container: HTMLElement): HTMLElement | null {
  const focusables = getFocusableElements(container);
  return focusables.length > 0 ? focusables[focusables.length - 1] : null;
}

/**
 * Trap focus within a container element
 * Prevents Tab from leaving the container
 * Returns an unsubscribe function
 */
export function trapFocus(container: HTMLElement): () => void {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    const focusables = getFocusableElements(container);
    if (focusables.length === 0) return;

    const activeElement = document.activeElement as HTMLElement;
    const focusedIndex = focusables.indexOf(activeElement);
    const firstFocusable = focusables[0];
    const lastFocusable = focusables[focusables.length - 1];

    if (e.shiftKey) {
      // Shift+Tab: move backwards
      if (activeElement === firstFocusable || focusedIndex <= 0) {
        e.preventDefault();
        setFocus(lastFocusable);
      }
    } else {
      // Tab: move forwards
      if (activeElement === lastFocusable || focusedIndex === focusables.length - 1) {
        e.preventDefault();
        setFocus(firstFocusable);
      }
    }
  };

  container.addEventListener('keydown', handleKeyDown);
  return () => container.removeEventListener('keydown', handleKeyDown);
}

/**
 * Announce a message to screen readers
 * Uses aria-live region for non-intrusive announcements
 */
export function announceMessage(message: string, type: 'polite' | 'assertive' = 'polite'): void {
  let region = document.querySelector(`[data-a11y-announce="${type}"]`) as HTMLElement;

  if (!region) {
    region = document.createElement('div');
    region.setAttribute('data-a11y-announce', type);
    region.setAttribute('aria-live', type);
    region.setAttribute('aria-atomic', 'true');
    region.className = 'sr-only';
    document.body.appendChild(region);
  }

  region.textContent = message;
  // Clear after announcement to allow same message to be announced again
  setTimeout(() => {
    region.textContent = '';
  }, 1000);
}

/**
 * Check if element is visible to screen readers
 * Returns false if element is hidden with display:none, visibility:hidden, etc.
 */
export function isAccessibilityVisible(element: HTMLElement): boolean {
  return (
    element.offsetParent !== null &&
    getComputedStyle(element).visibility !== 'hidden' &&
    getComputedStyle(element).display !== 'none'
  );
}

/**
 * Get accessible name of an element as computed by accessibility tree
 * Looks for aria-label, aria-labelledby, or text content
 */
export function getAccessibleName(element: HTMLElement): string {
  const ariaLabel = element.getAttribute('aria-label');
  if (ariaLabel) return ariaLabel;

  const ariaLabelledBy = element.getAttribute('aria-labelledby');
  if (ariaLabelledBy) {
    const labels = ariaLabelledBy.split(' ').map((id) => document.getElementById(id)?.textContent || '');
    return labels.join(' ');
  }

  const label = element.querySelector('label')?.textContent || '';
  if (label) return label;

  return element.textContent?.trim() || '';
}

/**
 * Create and focus a skip link programmatically
 * Useful for jumping to main content or landmarks
 */
export function focusTarget(targetSelector: string): void {
  const target = document.querySelector(targetSelector) as HTMLElement;
  if (target) {
    setFocus(target);
    target.setAttribute('tabindex', '-1');
  }
}