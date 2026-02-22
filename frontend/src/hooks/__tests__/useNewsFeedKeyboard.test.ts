import { renderHook, act } from '@testing-library/react';
import { useNewsFeedKeyboard } from '../useNewsFeedKeyboard';
import React from 'react';

describe('useNewsFeedKeyboard', () => {
  let containerRef: React.RefObject<HTMLDivElement>;

  beforeEach(() => {
    containerRef = React.createRef();
    containerRef.current = document.createElement('div');
  });

  describe('Initialization', () => {
    it('should initialize with focusedIndex as null', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));
      expect(result.current.focusedIndex).toBeNull();
    });

    it('should initialize with empty itemRefs array', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));
      expect(result.current.itemRefs.current).toEqual([]);
    });

    it('should return required functions', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));
      expect(typeof result.current.handleKeyDown).toBe('function');
      expect(typeof result.current.activatePanel).toBe('function');
      expect(typeof result.current.releasePanel).toBe('function');
    });
  });

  describe('Focus Management - Arrow Keys', () => {
    it('should move focus down with ArrowDown', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      // Setup items
      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      // Activate to start at index 0
      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      // Press ArrowDown
      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(1);
    });

    it('should move focus up with ArrowUp', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(1);

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('should wrap from last item to first with ArrowDown', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      // Navigate to last item
      for (let i = 0; i < 4; i++) {
        act(() => {
          const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
          Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
          result.current.handleKeyDown(event as any);
        });
      }

      expect(result.current.focusedIndex).toBe(4);

      // Wrap to first
      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('should wrap from first item to last with ArrowUp', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(4);
    });
  });

  describe('Focus Management - Home/End Keys', () => {
    it('should jump to first item with Home key', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      // Move to middle
      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'End' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(4);

      // Jump to home
      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'Home' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('should jump to last item with End key', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'End' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(4);
    });
  });

  describe('Focus Management - PageDown/PageUp Keys', () => {
    it('should advance by 5 items with PageDown', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(15, containerRef));

      const items = Array.from({ length: 15 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'PageDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(5);
    });

    it('should retreat by 5 items with PageUp', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(15, containerRef));

      const items = Array.from({ length: 15 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      // Jump to middle
      act(() => {
        result.current.activatePanel();
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'End' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(14);

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'PageUp' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(9);
    });

    it('should wrap with PageDown at end of list', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(12, containerRef));

      const items = Array.from({ length: 12 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      // Start at index 9
      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'End' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'PageUp' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(4);

      // Now PageDown from index 4
      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'PageDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(9);
    });
  });

  describe('Enter Key Behavior', () => {
    it('should click the article link when Enter is pressed', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(3, containerRef));

      const items = Array.from({ length: 3 }, () => document.createElement('div'));
      const anchors = items.map(() => document.createElement('a'));

      items.forEach((item, i) => {
        item.appendChild(anchors[i]);
        result.current.itemRefs.current[i] = item;
      });

      // Mock click
      anchors.forEach(anchor => {
        anchor.click = jest.fn();
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'Enter' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(anchors[0].click).toHaveBeenCalled();
    });

    it('should not click when Enter is pressed with no focus', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(3, containerRef));

      const items = Array.from({ length: 3 }, () => document.createElement('div'));
      const anchors = items.map(() => document.createElement('a'));

      items.forEach((item, i) => {
        item.appendChild(anchors[i]);
        result.current.itemRefs.current[i] = item;
      });

      anchors.forEach(anchor => {
        anchor.click = jest.fn();
      });

      // Don't activate, so focusedIndex is null
      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
      act(() => {
        result.current.handleKeyDown(event as any);
      });

      anchors.forEach(anchor => {
        expect(anchor.click).not.toHaveBeenCalled();
      });
    });

    it('should handle missing anchor element gracefully', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(2, containerRef));

      const items = Array.from({ length: 2 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'Enter' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(0);
    });
  });

  describe('Escape Key Behavior', () => {
    it('should release focus on Escape key', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(3, containerRef));

      const items = Array.from({ length: 3 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'Escape' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBeNull();
    });

    it('should blur the current focused item on Escape', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(3, containerRef));

      const items = Array.from({ length: 3 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        item.blur = jest.fn();
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'Escape' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(items[0].blur).toHaveBeenCalled();
    });
  });

  describe('Activation/Release', () => {
    it('activatePanel should set focusedIndex to 0 on first activation', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      expect(result.current.focusedIndex).toBeNull();

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('activatePanel should not reset focus if already focused', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(1);

      act(() => {
        result.current.activatePanel();
      });

      // Focus should stay at index 1
      expect(result.current.focusedIndex).toBe(1);
    });

    it('releasePanel should set focusedIndex to null', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      act(() => {
        result.current.releasePanel();
      });

      expect(result.current.focusedIndex).toBeNull();
    });
  });

  describe('List Refresh Behavior', () => {
    it('should clamp focusedIndex when item count decreases', () => {
      const { result, rerender } = renderHook(
        ({ count }) => useNewsFeedKeyboard(count, containerRef),
        { initialProps: { count: 10 } }
      );

      const items = Array.from({ length: 10 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      // Navigate to index 8
      for (let i = 0; i < 8; i++) {
        act(() => {
          const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
          Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
          result.current.handleKeyDown(event as any);
        });
      }

      expect(result.current.focusedIndex).toBe(8);

      // Simulate refresh with only 5 items
      rerender({ count: 5 });

      // focusedIndex should be clamped to 4
      expect(result.current.focusedIndex).toBe(4);
    });

    it('should clear focus when item count becomes 0', () => {
      const { result, rerender } = renderHook(
        ({ count }) => useNewsFeedKeyboard(count, containerRef),
        { initialProps: { count: 5 } }
      );

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);

      rerender({ count: 0 });

      expect(result.current.focusedIndex).toBeNull();
    });

    it('should preserve focusedIndex when item count increases', () => {
      const { result, rerender } = renderHook(
        ({ count }) => useNewsFeedKeyboard(count, containerRef),
        { initialProps: { count: 5 } }
      );

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(1);

      // Add more items
      rerender({ count: 10 });

      // focusedIndex should be preserved
      expect(result.current.focusedIndex).toBe(1);
    });
  });

  describe('Edge Cases - Empty List', () => {
    it('should not crash with empty item list', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(0, containerRef));

      expect(result.current.focusedIndex).toBeNull();

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBeNull();
    });

    it('should not move focus with empty item list', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(0, containerRef));

      const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
      Object.defineProperty(event, 'preventDefault', { value: jest.fn() });

      act(() => {
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBeNull();
    });
  });

  describe('Edge Cases - Single Item', () => {
    it('should activate single item', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(1, containerRef));

      const item = document.createElement('div');
      result.current.itemRefs.current[0] = item;

      act(() => {
        result.current.activatePanel();
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('should wrap navigation in single item list', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(1, containerRef));

      const item = document.createElement('div');
      result.current.itemRefs.current[0] = item;

      act(() => {
        result.current.activatePanel();
      });

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(0);
    });
  });

  describe('Event Prevention', () => {
    it('should prevent default on ArrowDown', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

      act(() => {
        result.current.handleKeyDown(event as any);
      });

      expect(preventDefaultSpy).toHaveBeenCalled();
    });

    it('should prevent default on all navigation keys', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      const keys = ['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageDown', 'PageUp', 'Enter', 'Escape'];

      keys.forEach(key => {
        const event = new KeyboardEvent('keydown', { key });
        const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

        act(() => {
          result.current.handleKeyDown(event as any);
        });

        expect(preventDefaultSpy).toHaveBeenCalled();
      });
    });
  });

  describe('Unknown Keys', () => {
    it('should ignore unknown keys', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));

      const items = Array.from({ length: 5 }, () => document.createElement('div'));
      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      const previousIndex = result.current.focusedIndex;

      const event = new KeyboardEvent('keydown', { key: 'a' });
      Object.defineProperty(event, 'preventDefault', { value: jest.fn() });

      act(() => {
        result.current.handleKeyDown(event as any);
      });

      expect(result.current.focusedIndex).toBe(previousIndex);
    });
  });

  describe('Focus Ref Updates', () => {
    it('should call focus on item when navigation occurs', () => {
      const { result } = renderHook(() => useNewsFeedKeyboard(3, containerRef));

      const items = Array.from({ length: 3 }, () => document.createElement('div'));
      const focusSpy = items.map(item => jest.spyOn(item, 'focus'));

      items.forEach((item, i) => {
        result.current.itemRefs.current[i] = item;
      });

      act(() => {
        result.current.activatePanel();
      });

      expect(focusSpy[0]).toHaveBeenCalled();

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
        result.current.handleKeyDown(event as any);
      });

      expect(focusSpy[1]).toHaveBeenCalled();
    });
  });
});
