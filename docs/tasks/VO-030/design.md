# VO-030: Timezone display bug in chart rendering for non-US locales

## Technical Design

Design spec written to `docs/tasks/VO-026/design.md`. Here's the summary:

---

**Root cause: two bugs, not one.**

**1. Backend — `analysis.py:164`**

```python
# Bug: uses server's local timezone (e.g. US/Eastern)
datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')

# Fix: always UTC-anchored
datetime.utcfromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
```

A US/Eastern server turns a 23:00 UTC timestamp into yesterday's date for anyone east of Greenwich. The raw `timestamp` UNIX field is already in the response and is timezone-neutral — no other API changes needed.

**2. Frontend — `PriceChart.tsx`**

The chart currently takes `time: string` (a `YYYY-MM-DD` date) and passes it straight to `lightweight-charts` with zero timezone context. No timezone indicator is shown. Fix:

- Pass `timestamp` (UNIX seconds) as `UTCTimestamp` (already exported by the library)
- Add a `localization.timeFormatter` callback using `Intl.DateTimeFormat` with the browser's detected timezone — no third-party date library needed
- Render a small timezone label (e.g., "All times in Europe/Berlin") to satisfy the visibility acceptance criterion

**Files to modify:** 3 total — `analysis.py`, `PriceChart.tsx`, and a new `test_chart_timezone.py`. The agents page cost chart passes `time: d.date` string and is unaffected.

**Testing:** Backend unit test asserts UTC-correct dates for a near-midnight timestamp. QA uses Chrome DevTools timezone override to verify GMT, CET, JST, AEST, IST without regressions on US locales.
