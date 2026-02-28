'use client';

import { useState, useEffect, useCallback } from 'react';
import { getState as fetchState, patchState } from '@/lib/api';

export interface UsePersistedStateResult {
  getState: <T>(key: string) => T | null;
  setState: (key: string, value: Record<string, unknown>) => void;
  isLoading: boolean;
}

export function usePersistedState(): UsePersistedStateResult {
  const [store, setStore] = useState<Record<string, Record<string, unknown>>>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchState()
      .then((data) => {
        if (!cancelled) setStore(data);
      })
      .catch(() => {
        // Degrade gracefully — each consumer hook falls back to its own default.
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const getStateKey = useCallback(
    <T>(key: string): T | null => (store[key] as T) ?? null,
    [store],
  );

  const setStateKey = useCallback(
    (key: string, value: Record<string, unknown>) => {
      setStore((prev) => ({ ...prev, [key]: value }));
      patchState({ [key]: value }).catch(() => {
        // Optimistic update already applied locally.
      });
    },
    [],
  );

  return { getState: getStateKey, setState: setStateKey, isLoading };
}