import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  getFocusableElements,
  setFocus,
  trapFocus,
  getFirstFocusable,
  getLastFocusable,
  announceMessage,
  isAccessibilityVisible,
  getAccessibleName,
} from '@/lib/a11y';

describe('A11y Utilities - Focus Management (WCAG 2.1 Level AA)', () => {
  let container: HTMLElement;

  beforeEach(() => {
    // Create a test container
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    if (container.parentNode) {
      document.body.removeChild(container);
    }
  });

  describe('getFocusableElements', () => {
    it('should find all focusable elements in container', () => {
      container.innerHTML = `
        <button>Button 1</button>
        <a href="#test">Link</a>
        <input type="text" placeholder="Input" />
        <select><option>Select</option></select>
        <textarea></textarea>
        <button disabled>Disabled Button</button>
      `;

      const focusables = getFocusableElements(container);

      // Should find 5 focusable elements (not the disabled button)
      expect(focusables.length).toBe(5);
      expect(focusables[0].tagName).toBe('BUTTON');
      expect(focusables[1].tagName).toBe('A');
      expect(focusables[2].tagName).toBe('INPUT');
    });

    it('should exclude hidden elements from focusable list', () => {
      container.innerHTML = `
        <button>Visible Button</button>
        <button style="display: none;">Hidden Button</button>
        <input type="text" style="visibility: hidden;" />
      `;

      const focusables = getFocusableElements(container);

      // Should only find the visible button
      expect(focusables.length).toBe(1);
      expect(focusables[0].textContent).toBe('Visible Button');
    });

    it('should include elements with positive tabindex', () => {
      container.innerHTML = `
        <div tabindex="0">Focusable Div</div>
        <div tabindex="1">Another Div</div>
        <div tabindex="-1">Non-focusable Div</div>
      `;

      const focusables = getFocusableElements(container);

      // Should find 2 elements (not tabindex="-1")
      expect(focusables.length).toBe(2);
    });
  });

  describe('setFocus & getFirstFocusable/getLastFocusable', () => {
    it('should focus element and call scrollIntoView', () => {
      const button = document.createElement('button');
      button.textContent = 'Test Button';
      container.appendChild(button);

      const scrollIntoViewSpy = vi.spyOn(button, 'scrollIntoView');

      setFocus(button);

      expect(document.activeElement).toBe(button);
      expect(scrollIntoViewSpy).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'center',
      });

      scrollIntoViewSpy.mockRestore();
    });

    it('should get first and last focusable elements', () => {
      container.innerHTML = `
        <button>First</button>
        <input type="text" />
        <a href="#test">Last</a>
      `;

      const first = getFirstFocusable(container);
      const last = getLastFocusable(container);

      expect(first?.textContent).toBe('First');
      expect(last?.textContent).toBe('Last');
    });

    it('should return null when no focusable elements exist', () => {
      container.innerHTML = '<div>No focusable elements</div>';

      expect(getFirstFocusable(container)).toBeNull();
      expect(getLastFocusable(container)).toBeNull();
    });

    it('should handle null input gracefully', () => {
      setFocus(null);
      // Should not throw error
      expect(true).toBe(true);
    });
  });

  describe('trapFocus - Keyboard Navigation (AC2: Keyboard Navigation)', () => {
    it('should wrap Tab to first element when on last focusable', () => {
      container.innerHTML = `
        <button id="first">Button 1</button>
        <button id="second">Button 2</button>
        <button id="last">Button 3</button>
      `;

      const firstButton = container.querySelector('#first') as HTMLElement;
      const lastButton = container.querySelector('#last') as HTMLElement;

      const unsubscribe = trapFocus(container);

      // Focus the last button
      lastButton.focus();
      expect(document.activeElement).toBe(lastButton);

      // Simulate Tab key press on last button
      const tabEvent = new KeyboardEvent('keydown', {
        key: 'Tab',
        bubbles: true,
        cancelable: true,
      });

      let preventDefaultCalled = false;
      vi.spyOn(tabEvent, 'preventDefault').mockImplementation(() => {
        preventDefaultCalled = true;
      });

      lastButton.dispatchEvent(tabEvent);

      // Focus should trap
      expect(preventDefaultCalled).toBe(true);

      unsubscribe();
    });

    it('should wrap Shift+Tab to last element when on first focusable', () => {
      container.innerHTML = `
        <button id="first">Button 1</button>
        <button id="second">Button 2</button>
        <button id="last">Button 3</button>
      `;

      const firstButton = container.querySelector('#first') as HTMLElement;

      const unsubscribe = trapFocus(container);

      // Focus the first button
      firstButton.focus();
      expect(document.activeElement).toBe(firstButton);

      // Simulate Shift+Tab key press on first button
      const shiftTabEvent = new KeyboardEvent('keydown', {
        key: 'Tab',
        shiftKey: true,
        bubbles: true,
        cancelable: true,
      });

      let preventDefaultCalled = false;
      vi.spyOn(shiftTabEvent, 'preventDefault').mockImplementation(() => {
        preventDefaultCalled = true;
      });

      firstButton.dispatchEvent(shiftTabEvent);

      // Focus should trap
      expect(preventDefaultCalled).toBe(true);

      unsubscribe();
    });

    it('should do nothing for non-Tab keys', () => {
      container.innerHTML = '<button>Button</button>';
      const button = container.querySelector('button') as HTMLElement;

      const unsubscribe = trapFocus(container);

      const enterEvent = new KeyboardEvent('keydown', {
        key: 'Enter',
        bubbles: true,
      });

      let preventDefaultCalled = false;
      vi.spyOn(enterEvent, 'preventDefault').mockImplementation(() => {
        preventDefaultCalled = true;
      });

      button.dispatchEvent(enterEvent);
      expect(preventDefaultCalled).toBe(false);

      unsubscribe();
    });

    it('should return unsubscribe function that removes listener', () => {
      container.innerHTML = '<button>Button</button>';
      const button = container.querySelector('button') as HTMLElement;

      const unsubscribe = trapFocus(container);
      expect(typeof unsubscribe).toBe('function');

      // After unsubscribe, event listener should be removed
      unsubscribe();

      const tabEvent = new KeyboardEvent('keydown', {
        key: 'Tab',
        bubbles: true,
      });

      let preventDefaultCalled = false;
      vi.spyOn(tabEvent, 'preventDefault').mockImplementation(() => {
        preventDefaultCalled = true;
      });

      button.dispatchEvent(tabEvent);

      // After unsubscribe, preventDefault should NOT be called
      expect(preventDefaultCalled).toBe(false);
    });
  });

  describe('announceMessage - Screen Reader Support (AC1: ARIA Labels)', () => {
    it('should create aria-live region with polite announcement', () => {
      announceMessage('Item saved successfully', 'polite');

      const region = document.querySelector('[data-a11y-announce="polite"]') as HTMLElement;
      expect(region).toBeDefined();
      expect(region.getAttribute('aria-live')).toBe('polite');
      expect(region.getAttribute('aria-atomic')).toBe('true');
      expect(region.textContent).toBe('Item saved successfully');
    });

    it('should create aria-live region with assertive announcement', () => {
      announceMessage('Error occurred', 'assertive');

      const region = document.querySelector('[data-a11y-announce="assertive"]') as HTMLElement;
      expect(region).toBeDefined();
      expect(region.getAttribute('aria-live')).toBe('assertive');
      expect(region.textContent).toBe('Error occurred');
    });

    it('should reuse existing aria-live region', () => {
      announceMessage('First message', 'polite');
      const firstRegion = document.querySelector('[data-a11y-announce="polite"]');

      announceMessage('Second message', 'polite');
      const secondRegion = document.querySelector('[data-a11y-announce="polite"]');

      // Should be same element (reused)
      expect(firstRegion).toBe(secondRegion);
      expect(secondRegion?.textContent).toBe('Second message');
    });

    it('should clear message after 1 second (accessibility best practice)', () => {
      vi.useFakeTimers();

      announceMessage('Temporary message', 'polite');
      const region = document.querySelector('[data-a11y-announce="polite"]') as HTMLElement;

      expect(region.textContent).toBe('Temporary message');

      vi.advanceTimersByTime(1100);

      expect(region.textContent).toBe('');

      vi.useRealTimers();
    });
  });

  describe('isAccessibilityVisible', () => {
    it('should return true for visible elements', () => {
      const button = document.createElement('button');
      button.textContent = 'Visible';
      container.appendChild(button);

      expect(isAccessibilityVisible(button)).toBe(true);
    });

    it('should return false for display:none elements', () => {
      const button = document.createElement('button');
      button.style.display = 'none';
      button.textContent = 'Hidden';
      container.appendChild(button);

      expect(isAccessibilityVisible(button)).toBe(false);
    });

    it('should return false for visibility:hidden elements', () => {
      const button = document.createElement('button');
      button.style.visibility = 'hidden';
      button.textContent = 'Hidden';
      container.appendChild(button);

      expect(isAccessibilityVisible(button)).toBe(false);
    });

    it('should return false when element not in document flow', () => {
      const button = document.createElement('button');
      button.textContent = 'Hidden';
      // Don't append to document

      expect(isAccessibilityVisible(button)).toBe(false);
    });
  });

  describe('getAccessibleName', () => {
    it('should prioritize aria-label for accessible name', () => {
      const button = document.createElement('button');
      button.setAttribute('aria-label', 'Close dialog');
      button.textContent = 'X'; // Should ignore text when aria-label exists
      container.appendChild(button);

      expect(getAccessibleName(button)).toBe('Close dialog');
    });

    it('should get name from element text content when no aria-label', () => {
      const button = document.createElement('button');
      button.textContent = 'Submit Form';
      container.appendChild(button);

      expect(getAccessibleName(button)).toBe('Submit Form');
    });

    it('should return empty string when no accessible name found', () => {
      const div = document.createElement('div');
      container.appendChild(div);

      expect(getAccessibleName(div)).toBe('');
    });

    it('should handle elements with aria-labelledby', () => {
      const label = document.createElement('div');
      label.id = 'label-id';
      label.textContent = 'Form Label';

      const input = document.createElement('input');
      input.setAttribute('aria-labelledby', 'label-id');

      container.appendChild(label);
      container.appendChild(input);

      expect(getAccessibleName(input)).toContain('Form Label');
    });
  });
});
