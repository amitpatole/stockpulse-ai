'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import type { RefObject } from 'react';

const PAGE_SIZE = 5;

interface UseNewsFeedKeyboardResult {
  focusedIndex: number | null;
  itemRefs: RefObject<(HTMLElement | null)[]>;
  handleKeyDown: (e: React.KeyboardEvent) => void;
  activatePanel: () => void;
  releasePanel: () => void;
}

export function useNewsFeedKeyboard(
  itemCount: number,
  containerRef: RefObject<HTMLDivElement | null>
): UseNewsFeedKeyboardResult {
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);
  const itemRefs = useRef<(HTMLElement | null)[]>([]);

  // Clamp focusedIndex when item count changes (e.g. after refresh)
  useEffect(() => {
    if (focusedIndex === null || itemCount === 0) return;
    const clamped = Math.min(focusedIndex, itemCount - 1);
    if (clamped !== focusedIndex) {
      setFocusedIndex(clamped);
      itemRefs.current[clamped]?.focus();
    }
  }, [itemCount]); // eslint-disable-line react-hooks/exhaustive-deps

  const focusAt = useCallback((idx: number) => {
    setFocusedIndex(idx);
    itemRefs.current[idx]?.focus();
  }, []);

  const activatePanel = useCallback(() => {
    if (focusedIndex === null && itemCount > 0) {
      focusAt(0);
    }
  }, [focusedIndex, itemCount, focusAt]);

  const releasePanel = useCallback(() => {
    setFocusedIndex(null);
    containerRef.current?.blur();
  }, [containerRef]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (itemCount === 0) return;

      const current = focusedIndex ?? -1;

      switch (e.key) {
        case 'ArrowDown': {
          e.preventDefault();
          const next = Math.min(current + 1, itemCount - 1);
          focusAt(next === -1 ? 0 : next);
          break;
        }
        case 'ArrowUp': {
          e.preventDefault();
          if (current <= 0) {
            focusAt(0);
          } else {
            focusAt(current - 1);
          }
          break;
        }
        case 'Home': {
          e.preventDefault();
          focusAt(0);
          break;
        }
        case 'End': {
          e.preventDefault();
          focusAt(itemCount - 1);
          break;
        }
        case 'PageDown': {
          e.preventDefault();
          const next = Math.min(Math.max(current, 0) + PAGE_SIZE, itemCount - 1);
          focusAt(next);
          break;
        }
        case 'PageUp': {
          e.preventDefault();
          const prev = Math.max(Math.max(current, 0) - PAGE_SIZE, 0);
          focusAt(prev);
          break;
        }
        case 'Enter': {
          e.preventDefault();
          if (focusedIndex !== null) {
            const anchor = itemRefs.current[focusedIndex]?.querySelector('a');
            anchor?.click();
          }
          break;
        }
        case 'Escape': {
          e.preventDefault();
          releasePanel();
          break;
        }
        default:
          break;
      }
    },
    [focusedIndex, itemCount, focusAt, releasePanel]
  );

  return { focusedIndex, itemRefs, handleKeyDown, activatePanel, releasePanel };
}
