# VO-026: Timezone display bug in chart rendering for non-US locales

## Technical Design

---

### Approach

Two-layer fix. The bug has two distinct root causes that must both be addressed:

1. **Backend (server-side date formatting):** `analysis.py:164` calls `datetime.fromtimestamp(timestamps[i])` with no timezone argument — this silently uses the server's local timezone. On a US/Eastern host, a UNIX timestamp at 23:00 UTC becomes `2024-02-13` instead of `2024-02-14`, corrupting dates for non-US users. Fix: replace with `datetime.utcfromtimestamp()` so the `date` field is always UTC-anchored. The raw `timestamp` field (UNIX epoch seconds) is already in the response and is timezone-neutral — no change needed there.

2. **Frontend (chart rendering):** `PriceChart.tsx` passes `time: string` (a `YYYY-MM-DD` date) directly to `lightweight-charts`. The chart receives no timezone context and shows no timezone indicator. Fix: pass the raw UNIX `timestamp` as a `UTCTimestamp`, configure the chart's `localization.timeFormatter` using `Intl.DateTimeFormat` with the browser's detected timezone, and render a visible timezone abbreviation label.

No architectural changes. No data model changes.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/api/analysis.py` | Line 164: `datetime.fromtimestamp(t)` → `datetime.utcfromtimestamp(t)` |
| `frontend/src/components/charts/PriceChart.tsx` | Accept `timestamp?: number`; use `UTCTimestamp` type; add `localization.timeFormatter` via `Intl.DateTimeFormat`; render timezone abbreviation label |
| `backend/tests/test_chart_timezone.py` | New: assert `date` fields in `/api/chart/<ticker>` response are UTC-anchored |

---

### Data Model Changes

None.

---

### API Changes

No new endpoints. The existing `GET /api/chart/<ticker>` response already includes a `timestamp` field (UNIX epoch seconds) alongside `date`. The `date` field will now be consistently UTC-formatted. Clients relying on `date` for display should be aware of this correction, but since the old behavior was wrong, this is a bugfix — not a breaking change.

---

### Frontend Changes

**`PriceChart.tsx`**

- Extend `PriceDataPoint` interface: add `timestamp?: number` (UNIX seconds).
- When `timestamp` is present, map data as `{ time: d.timestamp as UTCTimestamp, value: d.value }` instead of using the date string. `UTCTimestamp` is already exported from `lightweight-charts`.
- In `createChart` options, add a `localization` block:
  ```ts
  localization: {
    timeFormatter: (unixSeconds: number) => {
      return new Intl.DateTimeFormat(undefined, {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
        timeZoneName: 'short',
      }).format(new Date(unixSeconds * 1000));
    },
  },
  ```
- Below the chart container, render a small timezone label derived from `Intl.DateTimeFormat().resolvedOptions().timeZone` (e.g., "All times in Europe/Berlin"). This satisfies the acceptance criterion for a visible timezone indicator.

**Consumers:** The agents page passes `{ time: d.date, value: d.cost }` — this path uses the date-string branch and is unaffected. No changes needed in `app/agents/page.tsx`.

---

### Testing Strategy

- **Backend unit test (`test_chart_timezone.py`):** Mock `StockAnalytics.get_stock_price_data` to return a UNIX timestamp at `23:30 US/Eastern` (04:30 UTC next day). Assert the `date` field in the response matches the UTC date, not the Eastern date.
- **Frontend snapshot/unit:** Render `PriceChart` with `timestamp` fields; assert `localization.timeFormatter` is invoked and output contains a timezone abbreviation string.
- **QA manual:** Load the stock chart with browser timezone overridden (DevTools → Sensors) to GMT+1 (CET), JST (+9), AEST (+10), IST (+5:30). Confirm x-axis labels and tooltip timestamps reflect the correct local time and display a recognizable timezone token. Verify US/Eastern still renders correctly.
