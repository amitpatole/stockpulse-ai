# Technical Spec: Request Cancellation with AbortController

**Status**: Design Phase
**Severity**: Critical (Memory Leaks)
**Estimated Effort**: 3 story points

---

## 1. Approach

Implement AbortController integration across the API layer to cancel in-flight requests on:
1. **Component unmount** - Abort all active requests when hook cleanup runs
2. **Dependency change** - Abort previous request before fetching new data
3. **Manual cancel** - Expose cancel function for user-initiated aborts (e.g., stop long-running research)
4. **Retry exhaustion** - Abort after max retry attempts

**Core strategy**:
- Modify `api.ts:request()` to accept optional `signal: AbortSignal`
- Enhance `useApi.ts` hook to create `AbortController` per fetch, abort in cleanup
- Update all API client functions to thread signal through
- Add `abort()` method to `useApi` return value for manual cancellation

---

## 2. Files to Modify/Create

### Modify
- **`frontend/src/lib/api.ts`**
  - Line 31: Update `request<T>()` signature to accept `signal?: AbortSignal`
  - Line 34: Pass signal to fetch options: `signal: options?.signal`
  - Add `AbortError` detection in error handling (line 58)

- **`frontend/src/hooks/useApi.ts`**
  - Line 3: Add `useRef` (already imported)
  - Line 5: Add `abort` method to `UseApiResult<T>` interface
  - Line 20-21: Add `abortControllerRef = useRef<AbortController | null>(null)`
  - Line 26-45: Pass `signal` from controller to fetcher wrapper
  - Line 56-59: Abort controller in cleanup: `abortControllerRef.current?.abort()`
  - Line 62: Return `abort: () => abortControllerRef.current?.abort()`

### Create
- **`frontend/src/__tests__/useApi-abort.test.tsx`** (80 lines)
  - Test 1: Abort on unmount prevents state updates
  - Test 2: Abort on dependency change cancels previous request
  - Test 3: Manual abort stops ongoing request
  - Test 4: AbortError handled gracefully
  - Test 5: Multiple concurrent requests each get own AbortController

---

## 3. Data Model Changes

**None** - This is purely a client-side optimization. No backend changes.

---

## 4. API Changes

**None** - Existing endpoints unchanged. Signal is a client-side feature passed via fetch RequestInit.

---

## 5. Frontend Changes

### Modified Hook Interface
```typescript
interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  abort: () => void;  // NEW: manual cancellation
}
```

### Usage Example
```typescript
// Auto-abort on unmount (no changes needed)
const { data, loading, error } = useApi(() => fetchData());

// Manual abort (e.g., stop long-running research)
const { data, loading, abort } = useApi(() => generateResearch());
const handleCancel = () => {
  abort();  // Triggers AbortError → error state
};
```

### Affected Components (High-Priority for Testing)
- **`frontend/src/app/research/page.tsx`** - GenerateResearchBrief (long-running)
- **`frontend/src/components/dashboard/StockGrid.tsx`** - Multiple concurrent fetches
- **`frontend/src/components/dashboard/NewsFeed.tsx`** - Streaming news updates
- **`frontend/src/hooks/useSSE.ts`** - If exists, align signal passing

---

## 6. Testing Strategy

### Unit Tests: `useApi-abort.test.tsx`
| Test | Acceptance Criteria |
|------|-------------------|
| **Unmount abort** | Unmount triggers abort(), in-flight request cancelled, no state updates, error === null |
| **Dependency change abort** | Deps change → old request aborted, new request starts, old AbortController !== new |
| **Manual abort** | Call abort() → request cancelled, error contains "AbortError", loading → false |
| **Abort error handling** | AbortError doesn't set error state (expected), other errors do |
| **Concurrent requests** | Two useApi calls in same component each get unique AbortController, abort one ≠ abort other |

### Integration Tests
- **Memory leak test**: 100 mount/unmount cycles of research page, measure heap size stable (no growth)
- **Concurrent abort test**: Start 5 stock searches, abort 3 mid-request, verify 2 complete normally

### Acceptance Criteria
- ✅ All unit tests pass
- ✅ No requests continue after component unmount
- ✅ Memory stable across rapid mount/unmount
- ✅ Manual abort method callable and functional
- ✅ AbortError not logged as unexpected error

---

## Implementation Checklist

- [ ] Modify `api.ts:request()` to accept signal
- [ ] Modify `useApi.ts` to create/abort AbortController
- [ ] Write unit tests in `useApi-abort.test.tsx`
- [ ] Verify memory leaks fixed (DevTools heap snapshot)
- [ ] Manual abort works in research page
- [ ] All existing tests pass (no regression)
- [ ] Code review: signal threading, cleanup order
