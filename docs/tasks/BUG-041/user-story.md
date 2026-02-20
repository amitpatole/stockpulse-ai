# BUG-041: Timezone Display Bug in Scheduler for Non-US Locales

## User Story

**As a** non-US platform operator (e.g., in Europe or Asia), **I want** scheduler job times displayed in my local timezone with a clear timezone label, **so that** I can configure and monitor scheduled jobs without mentally converting from US Eastern Time and without risk of misconfiguring run times.

---

## Acceptance Criteria

**Backend (`scheduler.py` / `scheduler_routes.py`):**
- [ ] `next_run` is serialized as a valid ISO 8601 string with `T` separator and UTC offset (e.g., `2026-02-20T14:30:00+00:00`), not Python's default `str()` format
- [ ] API response includes an explicit `timezone` field on each job (the IANA name of the scheduler's configured timezone, e.g., `"America/New_York"`)
- [ ] The `trigger` string (or a new `trigger_tz` field) communicates which timezone cron hour/minute values are relative to

**Frontend (`scheduler/page.tsx`):**
- [ ] `formatDate()` reliably parses ISO 8601 strings (use `date.toISOString()` as input contract, not `str()`)
- [ ] "Next Run" and "Last Run" columns display time in the **browser's local timezone** (already attempted via `toLocaleDateString(undefined, ...)` — confirmed correct once ISO parsing is fixed)
- [ ] A timezone indicator badge/label is shown in the Scheduled Jobs table header or footer, e.g., `"Schedule times in America/New_York"`, so users understand what timezone the cron trigger is configured in
- [ ] No `Invalid Date` appears for any job with a valid `next_run_time`

**Testing:**
- [ ] Unit test: backend returns ISO 8601 `T`-separated string for `next_run`
- [ ] Unit test: `new Date(next_run)` in a simulated non-US locale parses without `NaN`
- [ ] Manual QA: verify "Next Run" in browser set to `Asia/Kolkata` shows correct local time

---

## Priority Reasoning

**Medium.** The app explicitly supports India market hours (`INDIA_MARKET_TIMEZONE = 'Asia/Kolkata'` in `config.py`), signalling non-US users are an intended audience. The bug causes incorrect time display and potential schedule misconfiguration for these users — a trust and correctness issue. Not P0 because the backend cron execution itself runs correctly; only the display is broken.

---

## Estimated Complexity: 2 / 5

Root cause is well-isolated: one serialization line in `get_all_jobs()` / `get_job()` (`str(sched_job.next_run_time)` → `.isoformat()`), plus a UI label addition. No schema changes, no new libraries. Risk is low. The only care needed is ensuring the `isoformat()` output is correctly consumed by the existing `formatDate()` function across browsers.
