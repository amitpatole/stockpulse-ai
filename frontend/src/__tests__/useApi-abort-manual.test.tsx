import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useApi } from '../hooks/useApi';

/**
 * Manual Abort & Concurrent Request Tests for useApi Hook
 *
 * Verifies that:
 * 1. Manual abort() method cancels in-flight requests
 * 2. AbortError from manual abort doesn't set error state (expected cancellation)
 * 3. Multiple concurrent useApi calls each get unique AbortController
 * 4. Aborting one request doesn't affect others
 * 5. State updates correctly after manual abort
 *
 * Acceptance Criteria from TECHNICAL_SPEC_REQUEST_CANCELLATION.md:
 * - AC1: Manual abort() callable and functional
 * - AC2: Concurrent requests each get unique AbortController
 * - AC3: AbortError not logged as unexpected error
 * - AC4: No state updates after manual abort
 */
describe('useApi - Manual Abort & Concurrent Requests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Manual Abort Method', () => {
    /**
     * AC1: Verify abort() method is exposed and callable
     * Happy Path: Call abort() on in-flight request, verify it cancels
     */
    it('should expose abort method and cancel in-flight request when called', async () => {
      let abortWasCalled = false;

      const fetcher = vi.fn((signal: AbortSignal) => {
        return new Promise(() => {
          // Simulate long-running request (e.g., research brief generation)
          signal.addEventListener('abort', () => {
            abortWasCalled = true;
          });
        });
      });

      const { result } = renderHook(() => useApi(fetcher));

      // Verify hook returns abort method
      expect(result.current.abort).toBeDefined();
      expect(typeof result.current.abort).toBe('function');

      // Wait for initial fetch to start
      await new Promise((resolve) => setTimeout(resolve, 10));

      // Call manual abort
      result.current.abort();

      // Allow abort event to propagate
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(abortWasCalled).toBe(true);
    });

    /**
     * AC1: Verify abort() has no effect when called on completed request
     * Edge Case: Calling abort after request completes should not error
     */
    it('should handle abort() gracefully when no request is pending', async () => {
      const fetcher = vi.fn((signal: AbortSignal) =>
        Promise.resolve({ data: 'completed' })
      );

      const { result } = renderHook(() => useApi(fetcher));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Calling abort on completed request should not throw
      expect(() => {
        result.current.abort();
      }).not.toThrow();

      // State should remain unchanged
      expect(result.current.data).toEqual({ data: 'completed' });
      expect(result.current.error).toBeNull();
    });

    /**
     * AC3: AbortError from manual abort should not set error state
     * Expected: AbortError is a normal cancellation, not a failure
     */
    it('should not set error state when manual abort is called', async () => {
      const fetcher = vi.fn((signal: AbortSignal) => {
        return new Promise(() => {
          // Hang until aborted
          signal.addEventListener('abort', () => {
            // Simulate fetch library throwing AbortError
            throw new DOMException('Request aborted', 'AbortError');
          });
        });
      });

      const { result } = renderHook(() => useApi(fetcher));

      await new Promise((resolve) => setTimeout(resolve, 10));

      // Manual abort
      result.current.abort();

      await new Promise((resolve) => setTimeout(resolve, 10));

      // Error should remain null (not set to AbortError)
      expect(result.current.error).toBeNull();
    });

    /**
     * AC1: Verify abort() is usable in user workflows (e.g., cancel research)
     * Integration: Simulate research page user clicking "Cancel" button
     */
    it('should allow canceling long-running operation like research generation', async () => {
      let operationStarted = false;
      let operationCancelled = false;

      const generateResearch = vi.fn((signal: AbortSignal) => {
        return new Promise(() => {
          operationStarted = true;
          signal.addEventListener('abort', () => {
            operationCancelled = true;
          });
          // Simulate long operation (5 second research generation)
          // In real scenario, would be streaming from server
        });
      });

      const { result } = renderHook(() => useApi(generateResearch));

      await waitFor(() => {
        expect(operationStarted).toBe(true);
      });

      // User clicks "Cancel Research" button
      result.current.abort();

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(operationCancelled).toBe(true);
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Concurrent Requests', () => {
    /**
     * AC2: Multiple concurrent useApi calls each get unique AbortController
     * Happy Path: Two useApi hooks in same component, verify different signals
     */
    it('should assign unique AbortController to each useApi call', async () => {
      const signals1: AbortSignal[] = [];
      const signals2: AbortSignal[] = [];

      const fetcher1 = vi.fn((signal: AbortSignal) => {
        signals1.push(signal);
        return Promise.resolve({ data: 'stocks' });
      });

      const fetcher2 = vi.fn((signal: AbortSignal) => {
        signals2.push(signal);
        return Promise.resolve({ data: 'news' });
      });

      const { result: result1 } = renderHook(() => useApi(fetcher1));
      const { result: result2 } = renderHook(() => useApi(fetcher2));

      await waitFor(() => {
        expect(result1.current.loading).toBe(false);
        expect(result2.current.loading).toBe(false);
      });

      // Each useApi call should have received a different signal
      expect(signals1.length).toBeGreaterThan(0);
      expect(signals2.length).toBeGreaterThan(0);
      expect(signals1[0]).not.toBe(signals2[0]);
    });

    /**
     * AC2: Aborting one request doesn't affect the other
     * Edge Case: Verify concurrent request isolation
     */
    it('should abort one request without affecting concurrent requests', async () => {
      const signals1: AbortSignal[] = [];
      const signals2: AbortSignal[] = [];
      const abortedSignals: AbortSignal[] = [];

      const fetcher1 = vi.fn((signal: AbortSignal) => {
        signals1.push(signal);
        signal.addEventListener('abort', () => {
          abortedSignals.push(signal);
        });
        return new Promise(() => {
          // Hang to test abort
        });
      });

      const fetcher2 = vi.fn((signal: AbortSignal) => {
        signals2.push(signal);
        return Promise.resolve({ data: 'news' });
      });

      const { result: result1 } = renderHook(() => useApi(fetcher1));
      const { result: result2 } = renderHook(() => useApi(fetcher2));

      await new Promise((resolve) => setTimeout(resolve, 10));

      // Both requests are in-flight
      expect(signals1.length).toBeGreaterThan(0);
      expect(signals2.length).toBeGreaterThan(0);

      // Abort only the first request
      result1.current.abort();

      await new Promise((resolve) => setTimeout(resolve, 10));

      // First request should be aborted
      expect(signals1[0].aborted).toBe(true);

      // Second request should NOT be aborted
      expect(signals2[0].aborted).toBe(false);

      // Second request should still have data
      expect(result2.current.data).toEqual({ data: 'news' });
    });

    /**
     * AC2: Multiple refetch + concurrent requests maintain isolation
     * Complex: 3 concurrent hooks, abort one in the middle, others continue
     */
    it('should handle 3+ concurrent requests with independent abort control', async () => {
      const hooks: ReturnType<typeof renderHook>[] = [];
      const signalsByHook: AbortSignal[][] = [[], [], []];

      const createFetcher = (index: number) =>
        vi.fn((signal: AbortSignal) => {
          signalsByHook[index].push(signal);
          return new Promise(() => {
            // All hang indefinitely
          });
        });

      // Create 3 concurrent hooks
      for (let i = 0; i < 3; i++) {
        const hook = renderHook(() => useApi(createFetcher(i)));
        hooks.push(hook);
      }

      await new Promise((resolve) => setTimeout(resolve, 10));

      // All should have different signals
      const signal0 = signalsByHook[0][0];
      const signal1 = signalsByHook[1][0];
      const signal2 = signalsByHook[2][0];

      expect(signal0).not.toBe(signal1);
      expect(signal1).not.toBe(signal2);
      expect(signal0).not.toBe(signal2);

      // Abort hook 1 (middle one)
      (hooks[1].result as any).current.abort();

      await new Promise((resolve) => setTimeout(resolve, 10));

      // Only hook 1 should be aborted
      expect(signal0.aborted).toBe(false);
      expect(signal1.aborted).toBe(true);
      expect(signal2.aborted).toBe(false);
    });
  });

  describe('Abort Error Handling', () => {
    /**
     * AC3: AbortError is not treated as unexpected error
     * Verify: Aborted request doesn't populate error state
     */
    it('should distinguish AbortError from real errors', async () => {
      const abortError = new DOMException('Request aborted', 'AbortError');
      let shouldAbort = false;

      const fetcher = vi.fn((signal: AbortSignal) => {
        if (shouldAbort) {
          return Promise.reject(abortError);
        }
        return Promise.resolve({ data: 'ok' });
      });

      const { result } = renderHook(() => useApi(fetcher));

      // First request succeeds
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBeNull();
      expect(result.current.data).toEqual({ data: 'ok' });

      // Set up to abort next request
      shouldAbort = true;

      // Trigger refetch
      result.current.refetch();

      await new Promise((resolve) => setTimeout(resolve, 10));

      // AbortError should not set error state
      expect(result.current.error).toBeNull();
    });

    /**
     * AC3: Regular errors are still caught and displayed
     * Verify: Non-AbortErrors still set error state correctly
     */
    it('should set error state for non-AbortError failures', async () => {
      const networkError = new Error('Network timeout');

      const fetcher = vi.fn((signal: AbortSignal) => {
        return Promise.reject(networkError);
      });

      const { result } = renderHook(() => useApi(fetcher));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Regular error should be set in error state
      expect(result.current.error).toBe('Network timeout');
      expect(result.current.data).toBeNull();
    });
  });

  describe('State Management After Abort', () => {
    /**
     * AC4: After abort, hook can still refetch and recover
     * Integration: Abort mid-request, then retry with refetch
     */
    it('should allow refetch after manual abort', async () => {
      const fetches: AbortSignal[] = [];

      const fetcher = vi.fn((signal: AbortSignal) => {
        fetches.push(signal);
        if (fetches.length === 1) {
          // First request hangs
          return new Promise(() => {});
        }
        // Second request (after refetch) succeeds
        return Promise.resolve({ data: 'recovered' });
      });

      const { result } = renderHook(() => useApi(fetcher));

      await new Promise((resolve) => setTimeout(resolve, 10));

      // First request in-flight
      expect(fetches.length).toBe(1);
      expect(result.current.loading).toBe(true);

      // Manual abort
      result.current.abort();

      await new Promise((resolve) => setTimeout(resolve, 10));

      // Abort worked
      expect(fetches[0].aborted).toBe(true);

      // Now refetch
      result.current.refetch();

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Second request should have succeeded
      expect(fetches.length).toBe(2);
      expect(result.current.data).toEqual({ data: 'recovered' });
      expect(result.current.error).toBeNull();
    });

    /**
     * Edge Case: Rapidly abort and refetch
     * Verify: Hook handles rapid state changes correctly
     */
    it('should handle rapid abort followed by refetch', async () => {
      let callCount = 0;

      const fetcher = vi.fn((signal: AbortSignal) => {
        callCount++;
        return new Promise((resolve) => {
          setTimeout(() => resolve({ data: `call-${callCount}` }), 50);
        });
      });

      const { result } = renderHook(() => useApi(fetcher));

      // Wait for first call
      await new Promise((resolve) => setTimeout(resolve, 10));

      // Immediately abort and refetch
      result.current.abort();
      result.current.refetch();

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should have 2 fetch calls (initial + refetch)
      expect(fetcher).toHaveBeenCalledTimes(2);
    });
  });
});
