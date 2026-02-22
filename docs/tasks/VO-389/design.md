# VO-389: Stale cache in stock detail page shows outdated data

## Technical Design

Now I have a clear picture of the actual codebase. Let me write the spec.

---

## VO-350 Technical Design Spec: Stale Cache in Stock Detail Page

### 1. Approach

Three distinct staleness bugs exist: (1) `sentiment_cache` serves up to 15-minute-old scores even after new `news` SSE events land, because invalidation is purely time-based with no event trigger; (2) the frontend `SentimentBadge` flags data stale at 60 minutes — 4× longer than the 15-minute backend TTL, creating a false "fresh" window; (3) the `snapshot` SSE event arrives on the frontend but does not bust the stock detail fetch, so page data can lag a full polling cycle. The fix adds event-driven cache invalidation in `sentiment_service.py`, aligns the frontend staleness threshold, and wires the `snapshot` SSE event to trigger a stock detail refetch.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/core/sentiment_service.py` — add `invalidate_ticker(ticker)` method that deletes the row from `sentiment_cache` for a given ticker
- **MODIFY**: `backend/api/sentiment.py` — call `invalidate_ticker()` when a `news` SSE event is dispatched for that ticker
- **MODIFY**: `backend/app.py` — after `send_sse_event("news", ...)` calls, invoke sentiment cache invalidation
- **MODIFY**: `frontend/src/components/stocks/SentimentBadge.tsx` — reduce staleness threshold from `60 * 60 * 1000` ms to `15 * 60 * 1000` ms (match backend TTL)
- **MODIFY**: `frontend/src/app/stocks/[ticker]/page.tsx` — subscribe to `useSSE` and call `refetch()` on `snapshot` or `news` events matching the current ticker
- **CREATE**: `backend/tests/test_stock_detail_cache.py` — regression tests

---

### 3. Data Model

No new tables. Existing `sentiment_cache` schema is sufficient. The fix operates on the existing row:

```sql
-- Existing schema (no change needed):
-- sentiment_cache(ticker TEXT PRIMARY KEY, score REAL, label TEXT, updated_at TEXT)

-- Invalidation is a targeted DELETE:
DELETE FROM sentiment_cache WHERE ticker = ?;
```

`ai_ratings` TTL (300s) is acceptable; no change required.

---

### 4. API Spec

No new endpoints. The fix is internal to the cache layer and SSE event flow.

`GET /api/stocks/<ticker>/sentiment` — existing endpoint, no signature change. Behavior change: a cache miss now triggers a fresh compute immediately after a `news` event, instead of waiting up to 15 minutes.

---

### 5. Frontend Component Spec

**SentimentBadge** (`frontend/src/components/stocks/SentimentBadge.tsx`)
- Change: `STALE_THRESHOLD_MS = 15 * 60 * 1000` (was `60 * 60 * 1000`)
- No new fields; existing `updated_at` drives the stale check

**Stock detail page** (`frontend/src/app/stocks/[ticker]/page.tsx`)
- Import `useSSE` hook (already available at `frontend/src/hooks/useSSE.ts`)
- Destructure `events` from `useSSE()`; add a `useEffect` watching `events`:
  - On event type `snapshot` or `news` where payload ticker matches route param → call `refetch()` from `useApi`
- Loading state: existing skeleton; no change
- Error state: existing error banner; no change

---

### 6. Verification

1. **Sentiment staleness**: Add a news article for AAPL via the DB directly, then immediately hit `GET /api/stocks/AAPL/sentiment` — confirm response `updated_at` reflects the recomputed timestamp, not a 15-minute-old cached value.
2. **SSE-triggered refetch**: Open the stock detail page in the browser, then push a `snapshot` SSE event via the debug endpoint — confirm the page data visibly refreshes without a manual reload (check Network tab for a new `/detail` request).
3. **Cross-ticker isolation**: Load the TSLA detail page, trigger a `news` event for AAPL — confirm TSLA's cached sentiment is NOT invalidated (cache key scoping holds).
