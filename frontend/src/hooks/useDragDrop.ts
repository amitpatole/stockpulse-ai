'use client';

import { useState, useCallback } from 'react';

interface DragItem {
  ticker: string;
  index: number;
}

export function useDragDrop(initialTickers: string[]) {
  const [tickers, setTickers] = useState(initialTickers);
  const [draggedItem, setDraggedItem] = useState<DragItem | null>(null);

  const handleDragStart = useCallback((ticker: string, index: number) => {
    setDraggedItem({ ticker, index });
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((targetTicker: string, targetIndex: number) => {
    if (!draggedItem) return;

    const newTickers = [...tickers];
    const draggedIndex = draggedItem.index;

    // Remove dragged item
    newTickers.splice(draggedIndex, 1);

    // Insert at new position
    const insertIndex = draggedIndex < targetIndex ? targetIndex - 1 : targetIndex;
    newTickers.splice(insertIndex, 0, draggedItem.ticker);

    setTickers(newTickers);
    setDraggedItem(null);

    return newTickers;
  }, [tickers, draggedItem]);

  const handleDragEnd = useCallback(() => {
    setDraggedItem(null);
  }, []);

  return {
    tickers,
    setTickers,
    draggedItem,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handleDragEnd,
  };
}