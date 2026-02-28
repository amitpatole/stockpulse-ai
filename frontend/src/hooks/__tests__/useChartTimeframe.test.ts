```typescript
/**
 * Test useChartTimeframe hook: single-timeframe selection with persistence.
 *
 * Coverage:
 * - AC1: Hook returns persisted timeframe when stored value is valid
 * - AC2: Hook returns default '1M' when no persisted state exists
 * - AC3: setTimeframe calls setState with correct key ('chart_timeframe') and value
 * - AC4: Falls back to default when persisted value is not a valid Timeframe
 * - AC5: Propagates isLoading flag from usePersistedState
 */

import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useChartTimeframe } from '../useChartTimeframe';
import * as persistedStateModule from '../usePersistedState';
import type { Timeframe } from '@/lib/types';

vi.mock('../usePersistedState');

const mockUsePersistedState = vi.mocked(persistedStateModule.usePersistedState);

describe('useChartTimeframe', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('AC1: Returns persisted timeframe when stored value is valid', () => {
    /**
     * When persisted state contains a valid timeframe ('1W'),
     * hook should return it instead of the default.
     */
    mockUsePersistedState.mockReturnValue({
      getState: vi.fn((key: string) =>
        key === 'chart_timeframe' ? { timeframe: '1W' } : null,
      ),
      setState: vi.fn(),
      isLoading: false,
    } as any);

    const { result } = renderHook(() => useChartTimeframe());

    expect(result.current.timeframe).toBe('1W');
    expect(result.current.isLoading).toBe(false);
  });

  it('AC2: Returns default 1M when no persisted state exists', () => {
    /**
     * When no persisted state exists (null),
     * hook should return the default timeframe '1M'.
     */
    mockUsePersistedState.mockReturnValue({
      getState: vi.fn(() => null),
      setState: vi.fn(),
      isLoading: false,
    } as any);

    const { result } = renderHook(() => useChartTimeframe());

    expect(result.current.timeframe).toBe('1M');
  });

  it('AC3: setTimeframe calls setState with correct key and value', () => {
    /**
     * When setTimeframe is called with a valid timeframe,
     * it should call setState with the 'chart_timeframe' key.
     */
    const mockSetState = vi.fn();
    mockUsePersistedState.mockReturnValue({
      getState: vi.fn(() => null),
      setState: mockSetState,
      isLoading: false,
    } as any);

    const { result } = renderHook(() => useChartTimeframe());

    act(() => {
      result.current.setTimeframe('3M' as Timeframe);
    });

    expect(mockSetState).toHaveBeenCalledWith('chart_timeframe', { timeframe: '3M' });
  });

  it('AC3: setTimeframe persists all valid timeframes', () => {
    /**
     * setTimeframe should persist any valid Timeframe value.
     */
    const mockSetState = vi.fn();
    mockUsePersistedState.mockReturnValue({
      getState: vi.fn(() => null),
      setState: mockSetState,
      isLoading: false,
    } as any);

    const { result } = renderHook(() => useChartTimeframe());

    const validTimeframes: Timeframe[] = ['1D', '1W', '1M', '3M', '6M', '1Y', '5Y', 'All'];
    for (const tf of validTimeframes) {
      act(() => {
        result.current.setTimeframe(tf);
      });
      expect(mockSetState).toHaveBeenCalledWith('chart_timeframe', { timeframe: tf });
    }
  });

  it('AC4: Falls back to 1M when persisted timeframe is not a valid Timeframe', () => {
    /**
     * When persisted state contains an unrecognized timeframe string,
     * hook should return the default '1M'.
     */
    mockUsePersistedState.mockReturnValue({
      getState: vi.fn(() => ({ timeframe: 'BOGUS_TF' })),
      setState: vi.fn(),
      isLoading: false,
    } as any);

    const { result } = renderHook(() => useChartTimeframe());

    expect(result.current.timeframe).toBe('1M');
  });

  it('AC4: Falls back to 1M when persisted state timeframe field is missing', () => {
    /**
     * When persisted state object has no 'timeframe' field,
     * hook should return the default '1M'.
     */
    mockUsePersistedState.mockReturnValue({
      getState: vi.fn(() => ({ other: 'data' })),
      setState: vi.fn(),
      isLoading: false,
    } as any);

    const { result } = renderHook(() => useChartTimeframe());

    expect(result.current.timeframe).toBe('1M');
  });

  it('AC5: Propagates isLoading flag from usePersistedState', () => {
    /**
     * The isLoading flag should reflect the persistence layer loading state.
     */
    mockUsePersistedState.mockReturnValue({
      getState: vi.fn(() => null),
      setState: vi.fn(),
      isLoading: true,
    } as any);

    const { result } = renderHook(() => useChartTimeframe());

    expect(result.current.isLoading).toBe(true);
  });
});
```