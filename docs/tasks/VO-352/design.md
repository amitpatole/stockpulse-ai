# VO-352: Create earnings calendar widget in market overview dashboard

## Technical Design

Here's the technical design spec:

---

### 1. Approach

Add an earnings calendar widget to the right-column sidebar of the market overview dashboard. The backend exposes a cached `earnings_events` SQLite table via a dedicated Flask blueprint (`GET /api/earnings`); the frontend `EarningsCalendar` component fetches that endpoint on mount and on-demand, rendering events as a scrollable list with date badges and watchlist highlights. Three gaps in the current implementation must be closed: ticker click navigation to the stock detail page, a stale-data warning indicator, and a watchlist-only filter toggle.

---

### 2. Files to Create/Modify

- **EXISTS**: `backend/api/earnings.py` — complete, no changes needed
- **EXISTS**: `backend/database.py` — `earnings_events` table + indices complete
- **EXISTS**: `backend/app.py` — `earnings_bp` already registered
- **EXISTS**: `frontend/src/lib/types.ts` — `EarningsEvent` / `EarningsResponse` complete
- **EXISTS**: `frontend/src/lib/api.ts` — `getEarnings(days)` complete
- **MODIFY**: `frontend/src/components/dashboard/EarningsCalendar.tsx` — add ticker click nav, stale indicator, watchlist filter toggle, fix default `days` to 7
- **EXISTS**: `frontend/src/app/page.tsx` — already renders `<EarningsCalendar />` in sidebar

---

### 3. Data Model

`earnings_events` is already defined:

```sql
CREATE TABLE IF NOT EXISTS earnings_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker         TEXT NOT NULL,
    company        TEXT,
    earnings_date  TEXT NOT NULL,       -- ISO date "2026-02-25"
    time_of_day    TEXT,                -- 'before_open' | 'after_close' | 'during_trading'
    eps_estimate   REAL,
    fiscal_quarter TEXT,
    fetched_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, earnings_date)
);
```

No new tables or columns required. Data population (ingestion agent) is out of scope for this ticket.

---

### 4. API Spec

**`GET /api/earnings?days=N`** — already implemented.

- `days`: int, 1–90, default 7
- Response `200`: `{ events: EarningsEvent[], stale: bool, as_of: string }`
- Events sorted: watchlist tickers first, then ascending `earnings_date`
- Always `200`; empty array on no data

---

### 5. Frontend Component Spec

**Component**: `EarningsCalendar` | **File**: `frontend/src/components/dashboard/EarningsCalendar.tsx`

| API field | UI element |
|---|---|
| `earnings_date` | Color-coded badge: amber = today, blue = tomorrow, slate = later |
| `ticker` | Bold white; wrapped in `<Link href="/stocks/{ticker}">` |
| `company` | Truncated sub-label, `text-slate-400` |
| `time_of_day` | Clock icon + `"Before Open"` / `"After Close"` / `"During Market"` |
| `eps_estimate` | `"Est. $X.XX"`, right-aligned; omitted if null |
| `on_watchlist` | Elevated card border + `TrendingUp` icon |
| `stale` (response) | Amber `AlertTriangle` icon in header with tooltip |

**Renders in**: `page.tsx` right sidebar below `<NewsFeed />` (already wired).

**Header controls**: day-range select (7/14/30, default **7**), watchlist-only toggle button, manual refresh button.

**Loading**: spinner + "Loading earnings…" | **Error**: inline red text, no full-page crash | **Empty**: icon + "No earnings in the next N days"

---

### 6. Verification

1. **Navigation** — click any ticker; confirm routing to `/stocks/{TICKER}` and the detail page loads.
2. **Watchlist filter** — toggle the filter; confirm list narrows to `on_watchlist === true` events; re-toggling restores all.
3. **Stale indicator** — insert an `earnings_events` row with `fetched_at` 2 hours ago; reload; confirm the amber warning icon appears in the widget header.

---

Saved to `docs/tasks/VO-362/design.md`. The core infrastructure is already shipped — the only file that needs modification is `EarningsCalendar.tsx` to close the three gaps (navigation, stale indicator, watchlist filter toggle) and fix the default window from 14d → 7d.
