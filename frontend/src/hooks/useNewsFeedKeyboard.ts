'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

const PAGE_SIZE = 5;

export function useNewsFeedKeyboard(
  itemCount: number,
  containerRef: React.RefObject<HTMLDivElement | null>
) {
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);
  const focusedIndexRef = useRef<number | null>(null);
  focusedIndexRef.current = focusedIndex;
  const itemRefs = useRef<(HTMLElement | null)[]>([]);

  // Clamp focusedIndex when the article list shrinks on refresh
  useEffect(() => {
    if (focusedIndex !== null && itemCount > 0) {
      const clamped = Math.min(focusedIndex, itemCount - 1);
      if (clamped !== focusedIndex) {
        setFocusedIndex(clamped);
        itemRefs.current[clamped]?.focus();
      }
    } else if (itemCount === 0) {
      setFocusedIndex(null);
    }
  }, [itemCount]); // eslint-disable-line react-hooks/exhaustive-deps

  const moveFocus = useCallback(
    (nextIndex: number) => {
      if (itemCount === 0) return;
      const wrapped = ((nextIndex % itemCount) + itemCount) % itemCount;
      setFocusedIndex(wrapped);
      itemRefs.current[wrapped]?.focus();
    },
    [itemCount]
  );

  const activatePanel = useCallback(() => {
    if (focusedIndexRef.current === null && itemCount > 0) {
      setFocusedIndex(0);
      itemRefs.current[0]?.focus();
    }
  }, [itemCount]);

  const releasePanel = useCallback(() => {
    setFocusedIndex(null);
    containerRef.current?.blur();
  }, [containerRef]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (itemCount === 0) return;

      const current = focusedIndex ?? -1;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          moveFocus(current + 1);
          break;
        case 'ArrowUp':
          e.preventDefault();
          moveFocus(current - 1);
          break;
        case 'Home':
          e.preventDefault();
          moveFocus(0);
          break;
        case 'End':
          e.preventDefault();
          moveFocus(itemCount - 1);
          break;
        case 'PageDown':
          e.preventDefault();
          moveFocus(current + PAGE_SIZE);
          break;
        case 'PageUp':
          e.preventDefault();
          moveFocus(current - PAGE_SIZE);
          break;
        case 'Enter':
          if (focusedIndex !== null) {
            e.preventDefault();
            const anchor = itemRefs.current[focusedIndex]?.querySelector('a');
            anchor?.click();
          }
          break;
        case 'Escape':
          e.preventDefault();
          releasePanel();
          break;
      }
    },
    [focusedIndex, itemCount, moveFocus, releasePanel]
  );

  return { focusedIndex, itemRefs, handleKeyDown, activatePanel, releasePanel };
}
