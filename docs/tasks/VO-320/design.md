# VO-320: Add social sentiment badge to stock detail page

## Technical Design

Now I have the full picture. Let me write the design spec.

---

## VO-369: Social Sentiment Badge — Technical Design Spec

### Approach

The infrastructure is largely built. `GET /api/stocks/<ticker>/sentiment` already exists, `sentiment_service.py` aggregates news + Reddit with 15-min SQLite caching, and `StockCard.tsx` already renders a sentiment meter from `AIRating`. The work is primarily **frontend-focused**: a new stock detail page + a proper badge component consuming the existing endpoint directly (not via the AI rating aggregate).

---

### Files to Modify / Create

| Action | Path |
|--------|------|
| **Create** | `frontend/src/app/stocks/[ticker]/page.tsx` — stock detail page |
| **Create** | `frontend/src/components/stocks/SentimentBadge.tsx` — badge + tooltip |
| **Modify** | `frontend/src/lib/api.ts` — add `getSentiment(ticker)` |
| **Modify** | `frontend/src/lib/types.ts` — add `SentimentData` interface |
| **Modify** | `frontend/src/components/dashboard/StockCard.tsx` — link ticker to detail page |
| **Verify** | `backend/api/sentiment.py` — confirm response shape matches spec |
| **Create** | `backend/tests/test_sentiment_api.py` — API + service tests |
| **Create** | `frontend/src/components/stocks/SentimentBadge.test.tsx` — component tests |

---

### Data Model Changes

**None.** `sentiment_cache` table already exists with `score`, `label`, `signal_count`, `sources` (JSON), `updated_at`. No schema migration needed.

---

### API Changes

Verify `backend/api/sentiment.py` returns exactly:
```json
{
  "ticker": "AAPL",
  "label": "bullish",
  "score": 0.72,
  "signal_count": 43,
  "sources": { "news": 38, "reddit": 5 },
  "updated_at": "2026-02-21T14:03:00Z",
  "stale": false
}
```
`stale: true` when `updated_at` is >15 min old (already in service). No endpoint changes expected; confirm and document.

---

### Frontend Changes

**`SentimentBadge` component:**
- Three states: Bullish (emerald), Bearish (red), Neutral (gray) — match existing `RATING_BG_CLASSES` pattern
- Displays `label` + `score * 100` rounded (e.g. "Bullish 72")
- Hover tooltip: source breakdown from `sources` object (News: 38, Reddit: 5)
- Stale indicator: amber pulsing dot if `stale === true`
- "No data" fallback if fetch fails or `signal_count === 0`
- Mobile-responsive via Tailwind flex/wrap

**`stocks/[ticker]/page.tsx`:**
- Header: ticker, name, current price (from existing `getRating(ticker)`)
- `SentimentBadge` adjacent to price — uses `useApi(getSentiment, { refreshInterval: 300_000 })` (5 min)
- SSE `rating_update` events trigger immediate refetch via `refetch()`

**`StockCard.tsx`:** Add `<Link href={/stocks/${ticker}}>` on ticker symbol.

**`types.ts`:**
```typescript
export interface SentimentData {
  ticker: string;
  label: 'bullish' | 'bearish' | 'neutral';
  score: number | null;
  signal_count: number;
  sources: { news: number; reddit: number };
  updated_at: string;
  stale: boolean;
}
```

---

### Testing Strategy

**Backend (`test_sentiment_api.py`):**
- Endpoint returns 200 with valid shape for a ticker with cached data
- Returns `"No data"` / graceful 200 (not 500) for unknown ticker
- `stale: true` when `updated_at` is 20 min old
- Cache hit behavior (second call within 15 min returns same `updated_at`)

**Frontend (`SentimentBadge.test.tsx`):**
- Renders Bullish/Bearish/Neutral with correct color classes
- Tooltip visible on hover with source counts
- Stale dot renders when `stale: true`
- "No data" renders when `score === null`
- No crash when fetch fails (error boundary fallback)
