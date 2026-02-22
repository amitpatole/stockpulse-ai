# VO-403: Timezone display bug in stock detail page for non-US locales

## Technical Design

### 1. Approach

Introduce a single `formatTime.ts` utility that wraps `Intl.DateTimeFormat` with explicit `timeZoneName: 'short'` — replacing the seven ad-hoc formatting functions scattered across components. All backend endpoints that serve the stock detail page will be audited to guarantee ISO 8601 strings with an explicit UTC offset (`+00:00`), eliminating ambiguous bare strings. A lightweight `TimezoneToggle` component on the stock detail page lets users switch between their browser (local) timezone and US Eastern time.

---

### 2. Files to Create/Modify

- **CREATE**: `frontend/src/lib/formatTime.ts` (centralized timezone-aware formatter)
- **CREATE**: `frontend/src/components/stocks/TimezoneToggle.tsx` (ET ↔ local toggle)
- **MODIFY**: `frontend/src/app/stocks/[ticker]/page.tsx` (render toggle, pass timezone to children)
- **MODIFY**: `frontend/src/components/dashboard/NewsFeed.tsx` (replace `timeAgo` with `formatTime`)
- **MODIFY**: `frontend/src/components/stocks/SentimentBadge.tsx` (replace `toLocaleString()` with `formatTime`)
- **MODIFY**: `frontend/src/components/agents/ActivityFeed.tsx` (replace `toLocaleTimeString` with `formatTime`)
- **MODIFY**: `frontend/src/lib/types.ts` (add `TimezoneMode = 'local' | 'ET'`)
- **MODIFY**: `backend/api/stocks.py` (candle timestamps: emit ISO 8601 UTC, not bare Unix seconds — or add `timestamp_iso` alongside `time`)
- **MODIFY**: `backend/api/news.py` (ensure `created_at`/`published_date` always carry `+00:00` suffix)

---

### 3. Data Model

No schema changes. Backend already stores UTC strings via `datetime.now(timezone.utc).isoformat()`. The one gap: `stocks.py` candles emit bare Unix integer seconds (`time`). Add a parallel `time_iso` field (`datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc).isoformat()`) to the candle dict so the frontend has an unambiguous ISO string.

---

### 4. API Spec

No new endpoints. Patch existing responses:

**`GET /api/stocks/<ticker>/detail`** — candle object gains:
```json
{ "time": 1708560000, "time_iso": "2026-02-22T09:30:00+00:00", "open": 182.5, ... }
```

**`GET /api/news`** — guarantee suffix on all timestamp strings:
```json
{ "created_at": "2026-02-22T14:32:05+00:00", "published_date": "2026-02-22T00:00:00+00:00" }
```

All other endpoints (`/api/earnings`, `/api/research/briefs`) already use `datetime.now(timezone.utc).isoformat()` which emits `+00:00` — no change needed.

---

### 5. Frontend Component Spec

**`formatTime.ts`** — exports two functions:
- `formatTimestamp(iso: string | null | undefined, tz: TimezoneMode): string` — returns `"14:32 CET"` / `"09:32 ET"`, or `"—"` on null/invalid
- `formatDate(iso: string | null | undefined, tz: TimezoneMode): string` — returns `"22 Feb 2026, 14:32 CET"`

Both use `new Intl.DateTimeFormat(undefined, { timeZone, timeZoneName: 'short', ... })`. ET maps to `"America/New_York"` (handles DST automatically). Invalid input catches `RangeError`/`NaN` and returns `"—"`.

**`TimezoneToggle.tsx`**
- Two-button pill: `Local` / `ET (Market)`
- Renders in the stock detail page header, right-aligned
- Exposes `onModeChange: (mode: TimezoneMode) => void`; parent holds state via `useState<TimezoneMode>('local')`
- Passes `tz` prop down to `NewsFeed`, `SentimentBadge`, `ActivityFeed`, and chart labels

**Stock detail page** (`/stocks/[ticker]/page.tsx`): renders `<TimezoneToggle>` in the existing page header row; threads `tz` state to child components.

---

### 6. Verification

1. **Non-US locale test**: Set browser language to `de-DE` (Germany). Open any stock detail page. Confirm all timestamps show `CET`/`CEST` label — no bare times, no `NaN`, no `Invalid Date`.
2. **Toggle test**: Click `ET (Market)` — confirm timestamps relabel to `ET` or `EST`/`EDT` depending on current DST state; click `Local` to revert.
3. **Null/missing data test**: Load a stock with no recent news (`published_date: null`). Confirm the date field renders `—` instead of `Invalid Date`.
