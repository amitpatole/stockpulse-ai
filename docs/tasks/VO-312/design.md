# VO-312: Support social sentiment badge in stock detail page

## Technical Design

---

## Technical Design Spec: Social Sentiment Badge

### 1. Approach

Aggregate sentiment from two **already-integrated** sources: the existing `news` table (articles already have NLP sentiment scores) and the Reddit scanner job (`/backend/jobs/`). A new `SentimentService` aggregates signals into a single score, cached in SQLite with a 15-minute TTL — matching the existing pattern in `analysis.py`. The badge lives in a new `SentimentBadge` component surfaced on `StockCard.tsx`.

No new third-party API dependencies are required for an MVP — we consume internal data already flowing through the system.

---

### 2. Files to Modify / Create

| Action | Path |
|--------|------|
| **Create** | `backend/core/sentiment_service.py` |
| **Create** | `backend/api/sentiment.py` (Flask blueprint) |
| **Modify** | `backend/app.py` — register new blueprint |
| **Modify** | `backend/database.py` — add `sentiment_cache` table |
| **Create** | `frontend/src/components/dashboard/SentimentBadge.tsx` |
| **Modify** | `frontend/src/components/dashboard/StockCard.tsx` — embed badge |
| **Modify** | `frontend/src/lib/api.ts` — add `getSentiment(ticker)` |
| **Modify** | `frontend/src/lib/types.ts` — add `SentimentPayload` type |
| **Create** | `backend/tests/test_sentiment_service.py` |

---

### 3. Data Model Changes

New table in `backend/database.py`:

```sql
CREATE TABLE IF NOT EXISTS sentiment_cache (
    ticker          TEXT PRIMARY KEY,
    score           REAL NOT NULL,          -- 0.0–1.0 (bullish proportion)
    label           TEXT NOT NULL,          -- 'bullish' | 'bearish' | 'neutral'
    signal_count    INTEGER NOT NULL,
    sources         TEXT NOT NULL,          -- JSON: {"news": n, "reddit": n}
    updated_at      TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sentiment_ticker ON sentiment_cache(ticker);
```

No changes to existing tables. Sentiment score in `ai_ratings` remains independent (model-derived); this is signal-aggregated.

---

### 4. API Changes

**New endpoint** — `backend/api/sentiment.py`:

```
GET /api/stocks/<ticker>/sentiment
```

Response (200):
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

Response (200, no data):
```json
{ "ticker": "AAPL", "label": "neutral", "score": null, "signal_count": 0 }
```

Cache logic mirrors `_get_cached_ratings()` in `analysis.py`: read from `sentiment_cache`, recompute if `updated_at` > 15 min ago, write back.

---

### 5. Frontend Changes

**`SentimentBadge.tsx`** — standalone component:
- Props: `ticker: string`
- Fetches `GET /api/stocks/<ticker>/sentiment` via `useApi` hook (15-min poll interval)
- Renders pill badge: green/red/grey + label + score percentage
- Tooltip on hover: source breakdown + last updated timestamp
- Graceful empty state: grey "No data" pill — no spinner loop

**`StockCard.tsx`** — insert `<SentimentBadge ticker={stock.ticker} />` below the price/rating header row.

**`types.ts`** — add:
```typescript
interface SentimentPayload {
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

### 6. Testing Strategy

**`backend/tests/test_sentiment_service.py`** (pytest):
- Unit: score → label mapping boundaries (e.g., score 0.55 = neutral vs bullish threshold)
- Unit: cache hit skips recomputation (mock `updated_at` within TTL)
- Unit: cache miss triggers aggregation (mock `updated_at` > 15 min)
- Unit: zero signals → `score=null`, label `neutral`, no crash
- Unit: `sources` JSON breakdown accuracy (news-only, reddit-only, mixed)
- Integration: HTTP `GET /api/stocks/AAPL/sentiment` returns valid schema (use `in_memory_db` fixture)

**Frontend**: Manual smoke test on `StockCard` — badge renders, tooltip shows, "No data" state degrades cleanly.

---

**Spike deferred**: Stocktwits/Twitter integration is explicitly out of scope for this iteration. The Reddit path only activates if the existing Reddit scanner job is enabled in settings.
