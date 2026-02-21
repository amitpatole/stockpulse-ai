# VO-368: Timezone display bug in scheduler configuration for non-US locales

## Technical Design

## VO-367: Timezone Display Bug — Technical Design Spec

---

### 1. Approach

UTC storage is already correct — APScheduler persists triggers in `MARKET_TIMEZONE` (default `US/Eastern`) and the SQLite jobstore handles the rest. The bug is purely in the **API response and display layer**: `next_run` timestamps are returned without timezone context, and the frontend renders them without conversion, silently showing ET times to non-US users.

**Strategy**: Surface a `timezone` field from the API; let the browser convert UTC timestamps to the user's local timezone at render time. No DB schema changes. No changes to how triggers are stored or executed.

---

### 2. Files to Modify

| File | Change |
|---|---|
| `backend/api/scheduler_routes.py` | Add `timezone` field to job response serialization |
| `backend/scheduler.py` | Expose `get_scheduler_timezone()` helper method on `SchedulerManager` |
| `frontend/src/lib/api.ts` | Add `trigger_args` and `timezone` to `ScheduledJob` type |
| `frontend/src/app/scheduler/page.tsx` | Update `formatDate()` to use `Intl.DateTimeFormat` with user locale; show timezone label |

---

### 3. Data Model Changes

**None.** UTC storage is correct. `job_history.executed_at` already uses `CURRENT_TIMESTAMP` (UTC). APScheduler's own jobstore table is unchanged.

---

### 4. API Changes

**`GET /api/scheduler/jobs`** and **`GET /api/scheduler/jobs/<job_id>`** — add one field to each job object:

```json
{
  "id": "morning_briefing",
  "next_run": "2026-02-22T13:30:00+00:00",
  "trigger_args": {"hour": 8, "minute": 30, "day_of_week": "mon-fri"},
  "timezone": "America/New_York"
}
```

- `next_run` must be returned as a **timezone-aware ISO 8601 string** (APScheduler already produces this; ensure it's serialized with offset, not stripped to naive).
- `timezone` is the IANA name of the scheduler's configured timezone — sourced from the live APScheduler instance, not `Config`, to reflect actual runtime state.

In `scheduler.py`, add:
```python
def get_scheduler_timezone(self) -> str:
    return str(self._scheduler.timezone)
```

In `scheduler_routes.py`, include `'timezone': scheduler_manager.get_scheduler_timezone()` in every job dict returned by `list_jobs()` and `get_job()`.

---

### 5. Frontend Changes

**`frontend/src/lib/api.ts`** — extend `ScheduledJob`:
```typescript
timezone: string;           // IANA name, e.g. "America/New_York"
trigger_args: Record<string, unknown>;
```

**`frontend/src/app/scheduler/page.tsx`** — replace `formatDate()`:
```typescript
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium', timeStyle: 'short', timeZone: undefined // browser local
  }).format(new Date(dateStr));
}
```

Add a small timezone badge to the Schedule column header: `Schedule (your local time)`. For the trigger display, append the configured server timezone label (e.g., `08:30 ET`) sourced from `job.timezone`, so users can cross-reference.

---

### 6. Testing Strategy

**Unit tests** (`backend/tests/test_scheduler_timezone.py`, new file):
- `test_list_jobs_includes_timezone_field` — assert `timezone` key present and valid IANA string
- `test_get_job_includes_timezone_field` — same for single-job endpoint
- `test_next_run_is_timezone_aware` — assert `next_run` parses to an aware datetime (has UTC offset)
- Parameterize scheduler init with `CET`, `Asia/Kolkata`, `Asia/Tokyo`, `America/Sao_Paulo` to cover all four acceptance-criteria locales

**Regression**: Run existing `test_scheduler_race_condition.py` (45 tests) — must stay green. The new field is additive; no existing assertions should break.

**Manual QA**: Set `MARKET_TIMEZONE=CET` in env, verify browser in IST locale shows correct local times for `morning_briefing` and `daily_summary` jobs.
