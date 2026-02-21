# VO-316: Add earnings calendar widget to market overview dashboard

## Technical Design

---

## VO-314: Earnings Calendar Widget — Technical Design Spec

### Approach

Cache earnings data in SQLite via a daily background job. Serve it through a new REST endpoint. Render a new dashboard widget following the `NewsFeed` pattern (fetch-and-display, `useApi` hook, skeleton/error/empty states). No real-time updates needed — daily refresh with a staleness indicator suffices.

Use **yfinance** as the v1 data source (`yf.Ticker(symbol).calendar` returns next earnings date/EPS estimates at no cost). This avoids a paid API dependency while matching our existing provider-first strategy.

---

### Files to Modify / Create

| Action | Path |
|--------|------|
| **Modify** | `backend/database.py` — add `earnings_events` table in `init_all_tables()` |
| **Create** | `backend/api/earnings.py` — new Blueprint |
| **Modify** | `backend/app.py` — register `earnings_bp` |
| **Create** | `backend/jobs/earnings_refresh.py` — daily cache job |
| **Modify** | `backend/jobs/__init__.py` — register job via `register_all_jobs()` |
| **Create** | `frontend/src/components/dashboard/EarningsCalendar.tsx` — widget |
| **Modify** | `frontend/src/lib/api.ts` — add `getEarnings(days)` |
| **Modify** | `frontend/src/lib/types.ts` — add `EarningsEvent` interface |
| **Modify** | `frontend/src/app/page.tsx` — mount widget in dashboard |
| **Create** | `backend/tests/test_earnings_calendar.py` |

---

### Data Model

```sql
CREATE TABLE IF NOT EXISTS earnings_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker       TEXT NOT NULL,
    company_name TEXT,
    report_date  TEXT NOT NULL,          -- ISO date: YYYY-MM-DD
    timing       TEXT DEFAULT 'unconfirmed', -- 'BMO' | 'AMC' | 'unconfirmed'
    eps_estimate REAL,                   -- NULL if unavailable
    fetched_at   TEXT NOT NULL,          -- ISO datetime, staleness check
    UNIQUE(ticker, report_date)
);
CREATE INDEX IF NOT EXISTS idx_earnings_report_date ON earnings_events(report_date);
```

---

### API Changes

**New endpoint:** `GET /api/earnings?days=7`

- `days` param: `7` (default) | `14` | `30`
- Returns events in window `[today, today + days)`, sorted by `report_date ASC`, then `ticker ASC`
- Response includes `last_updated` (oldest `fetched_at` in result set) for footer display
- Returns `[]` with `last_updated: null` on empty — no 404

```json
{
  "events": [
    { "ticker": "AAPL", "company_name": "Apple Inc.", "report_date": "2026-02-25",
      "timing": "AMC", "eps_estimate": 2.31 }
  ],
  "last_updated": "2026-02-21T09:00:00",
  "window_days": 7
}
```

---

### Frontend Changes

**`EarningsCalendar.tsx`** — mirrors `NewsFeed.tsx` structure:
- `useApi(() => getEarnings(days), [], { refreshInterval: 3_600_000 })` (hourly client refresh, data is daily)
- Days selector: segmented control (`7 | 14 | 30`), drives re-fetch
- Stale data flag: if `last_updated` > 24h ago, show amber warning badge in footer
- Row: ticker (link → `/research?ticker=AAPL`), company name, date, timing badge, EPS estimate or `—`
- Empty state: "No earnings in the next {days} days for tracked stocks"
- Widget dismiss/minimize: matches existing pattern used by other dashboard widgets

**`page.tsx`** — add `<EarningsCalendar />` in the right column below `NewsFeed`, or as a collapsible section in the main grid.

---

### Testing Strategy

**`test_earnings_calendar.py`** — pytest, same patterns as existing test files:

1. **Schema** — `init_all_tables()` creates table; `UNIQUE(ticker, report_date)` enforced; upsert on conflict
2. **API endpoint** — `days` filtering (7/14/30), chronological sort, alphabetical tiebreak, empty result, stale flag in response
3. **Refresh job** — mocked yfinance returns; inserts new rows; upserts on re-run (no duplicates); only fetches tickers in `stocks` table
4. **Staleness** — `fetched_at` > 24h triggers `is_stale: true` in response
5. **Edge cases** — `eps_estimate` NULL when unavailable, `timing` defaults to `'unconfirmed'`, window excludes today + `days`

No concurrency tests needed — the refresh job runs single-threaded on a daily cron; the endpoint is read-only.
