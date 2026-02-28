'use client';

import { useCallback } from 'react';
import type { Timeframe } from '@/lib/types';
import { usePersistedState } from './usePersistedState';

const STATE_KEY = 'chart_timeframe';
const DEFAULT_TIMEFRAME: Timeframe = '1M';
const VALID_TIMEFRAMES: Timeframe[] = ['1D', '1W', '1M', '3M', '6M', '1Y', '5Y', 'All'];

interface PersistedChartTimeframe {
  timeframe?: string;
}

function isValidTimeframe(val: unknown): val is Timeframe {
  return typeof val === 'string' && (VALID_TIMEFRAMES as string[]).includes(val);
}

export interface UseChartTimeframeResult {
  timeframe: Timeframe;
  setTimeframe: (tf: Timeframe) => void;
  isLoading: boolean;
}

export function useChartTimeframe(): UseChartTimeframeResult {
  const { getState, setState, isLoading } = usePersistedState();

  const raw = getState<PersistedChartTimeframe>(STATE_KEY);
  const timeframe: Timeframe = isValidTimeframe(raw?.timeframe)
    ? (raw!.timeframe! as Timeframe)
    : DEFAULT_TIMEFRAME;

  const setTimeframe = useCallback(
    (tf: Timeframe) => {
      setState(STATE_KEY, { timeframe: tf });
    },
    [setState],
  );

  return { timeframe, setTimeframe, isLoading };
}