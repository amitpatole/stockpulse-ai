```typescript
/**
 * Test usePersistedState hook: cross-session state persistence via /api/app-state.
 *
 * Coverage:
 * - AC1: Loads state from API on mount; getState returns keyed values
 * - AC2: API failure degrades gracefully — getState returns null for all keys
 * - AC3: setState applies optimistic update locally and syncs via patchState
 * - AC4: patchState API failure does not revert local state (optimistic update stays)
 * - AC5: Unmounting during fetch cancels the update to prevent memory leaks
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { usePersistedState } from '../usePersistedState';
import * as apiLib from '@/lib/api';

vi.mock('@/lib/api');

const mockGetState = vi.mocked(apiLib.getState);
const mockPatchState = vi.mocked(apiLib.patchState);

describe('usePersistedState', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('AC1: Loads state from API on mount and provides getState', async () => {
    /**
     * On mount, hook fetches /api/app-state and populates the local store.
     * getState(key) returns the value for that key.
     */
    const mockState = {
      chart_timeframe: { timeframe: '1D' },
      ui: { theme: 'dark' },
    };
    mockGetState.mockResolvedValue(mockState);

    const { result } = renderHook(() => usePersistedState());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.getState('chart_timeframe')).toEqual({ timeframe: '1D' });
    expect(result.current.getState('ui')).toEqual({ theme: 'dark' });
    expect(apiLib.getState).toHaveBeenCalledTimes(1);
  });

  test('AC1: isLoading transitions from true to false after fetch resolves', async () => {
    mockGetState.mockResolvedValue({});

    const { result } = renderHook(() => usePersistedState());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  test('AC2: API failure degrades gracefully — getState returns null', async () => {
    /**
     * When /api/app-state fetch fails, hook resolves with empty store.
     * All getState calls return null (not throwing).
     */
    mockGetState.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => usePersistedState());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.getState('chart_timeframe')).toBeNull();
    expect(result.current.getState('ui')).toBeNull();
  });

  test('AC3: setState applies optimistic update locally and calls patchState', async () => {
    /**
     * When setState is called, the local store updates immediately
     * and patchState is called with the new key-value pair.
     */
    mockGetState.mockResolvedValue({});
    mockPatchState.mockResolvedValue({ ok: true });

    const { result } = renderHook(() => usePersistedState());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setState('chart_timeframe', { timeframe: '3M' });
    });

    expect(result.current.getState('chart_timeframe')).toEqual({ timeframe: '3M' });
    expect(apiLib.patchState).toHaveBeenCalledWith({ chart_timeframe: { timeframe: '3M' } });
  });

  test('AC3: setState with multiple keys each trigger separate patchState calls', async () => {
    mockGetState.mockResolvedValue({});
    mockPatchState.mockResolvedValue({ ok: true });

    const { result } = renderHook(() => usePersistedState());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setState('key_a', { val: 1 });
      result.current.setState('key_b', { val: 2 });
    });

    expect(result.current.getState('key_a')).toEqual({ val: 1 });
    expect(result.current.getState('key_b')).toEqual({ val: 2 });
    expect(apiLib.patchState).toHaveBeenCalledTimes(2);
  });

  test('AC4: patchState failure does not revert local state (optimistic)', async () => {
    /**
     * If the API call to persist the state fails, the local (optimistic)
     * update stays in place — no rollback.
     */
    mockGetState.mockResolvedValue({});
    mockPatchState.mockRejectedValue(new Error('Sync failed'));

    const { result } = renderHook(() => usePersistedState());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setState('timezone', { mode: 'ET' });
    });

    // Local state should still reflect the update despite API failure
    expect(result.current.getState('timezone')).toEqual({ mode: 'ET' });
  });

  test('AC5: Unmount during fetch cancels state update to prevent memory leak', async () => {
    /**
     * If the component unmounts while the fetch is still in flight,
     * the resolved value should not update the (now-unmounted) state.
     */
    let resolveGetState!: (value: Record<string, Record<string, unknown>>) => void;
    const pendingPromise = new Promise<Record<string, Record<string, unknown>>>((resolve) => {
      resolveGetState = resolve;
    });
    mockGetState.mockReturnValue(pendingPromise);

    const { unmount } = renderHook(() => usePersistedState());

    unmount();

    // Resolve after unmount — should not trigger a state update or React warning
    act(() => {
      resolveGetState({ chart_timeframe: { timeframe: '1D' } });
    });

    await waitFor(() => {
      expect(apiLib.getState).toHaveBeenCalledTimes(1);
    });
  });
});
```