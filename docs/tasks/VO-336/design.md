# VO-336: Support social sentiment badge in stock detail page

## Technical Design

Good — the backend is already fully wired: the sentiment endpoint exists, the blueprint is registered, `SentimentData` type is defined, and `getStockSentiment()` is in `api.ts`. This is a pure frontend task.

---

## VO-386: Social Sentiment Badge — Technical Design Spec

### 1. Approach

The backend contract is already complete (`GET /api/stocks/<ticker>/sentiment`, `SentimentData` type, `getStockSentiment()` client function). This spec is entirely a frontend concern: create an isolated `SentimentBadge` component that fetches sentiment independently on mount and renders inline with the price header on the stock detail page. The component handles its own loading, error, and stale states so the existing quote fetch is not disturbed.

---

### 2. Files to Create/Modify

- **CREATE**: `frontend/src/components/stocks/SentimentBadge.tsx`
- **MODIFY**: `frontend/src/app/stocks/[ticker]/page.tsx` — import and render `SentimentBadge` in the price header row

No backend files require changes. No type or API changes needed.

---

### 3. Data Model

No new tables or columns. Sentiment data is aggregated at query time by `backend/core/sentiment_service.py` from the existing `news` table and Reddit agent run outputs. Cache TTL is 15 minutes (in-memory, server-side).

---

### 4. API Spec

Endpoint already exists — no changes needed.

```
GET /api/stocks/{ticker}/sentiment

200 OK
{
  "ticker":       "AAPL",
  "label":        "bullish" | "neutral" | "bearish",
  "score":        0.72 | null,
  "signal_count": 43,
  "sources":      { "news": 38, "reddit": 5 },
  "updated_at":   "2026-02-21T14:03:00Z",
  "stale":        false
}
```

Stale detection: `updated_at` older than 1 hour, or `stale: true` from server.

---

### 5. Frontend Component Spec

**Component**: `SentimentBadge`
**File**: `frontend/src/components/stocks/SentimentBadge.tsx`

**Props**: `{ ticker: string }`

**Data mapping**:

| API field | UI element |
|---|---|
| `label` | Badge text (`Bullish` / `Neutral` / `Bearish`) + color class |
| `score` | Formatted score (`+0.72`, `-0.31`, `—` when null) |
| `sources` | Source line: `News · Reddit` with counts |
| `stale` or age > 1hr | Warning icon (⚠) beside badge |
| `signal_count` | Tooltip: "43 signals" |
| `updated_at` | Tooltip: formatted timestamp |

**Color classes** (using existing Tailwind palette):
- `bullish` → `bg-emerald-500/15 text-emerald-400 border-emerald-500/30`
- `neutral` → `bg-slate-500/15 text-slate-400 border-slate-500/30`
- `bearish` → `bg-red-500/15 text-red-400 border-red-500/30`

**Tooltip** (native `title` attribute or lightweight hover div): score, source breakdown (`News: 38, Reddit: 5`), signal count, last updated.

**Loading state**: single pulse skeleton (`h-7 w-28 animate-pulse rounded-full bg-slate-800`).

**Error / no-data state**: small muted badge reading `No sentiment data` in `text-slate-500`.

**Where it renders**: `frontend/src/app/stocks/[ticker]/page.tsx` — inserted into the `flex items-baseline gap-3` row alongside the price and change-pct badge (line 78), so it sits inline in the price header on all viewports. On mobile the `flex-wrap` on that row naturally pushes it to the next line.

**Fetch**: `useApi(() => getStockSentiment(ticker), [ticker])` — same `useApi` hook pattern used throughout the page.

---

### 6. Verification

1. **Happy path**: Navigate to `/stocks/AAPL` — badge appears next to the price with a coloured label, score (e.g. `+0.72`), and source line. Hovering shows the tooltip with signal count and timestamp.
2. **Stale warning**: Manually set `updated_at` in the sentiment service to >1hr ago (or set `stale: true`) — confirm the ⚠ icon appears on the badge without breaking the rest of the UI.
3. **No-data fallback**: Call the endpoint for a ticker with no news or Reddit signals — confirm the badge renders `No sentiment data` in muted text rather than erroring or showing `null`.
