# VO-349: Stale cache in scheduler configuration shows outdated data

## Technical Design

Now I have everything I need. Here's the technical design spec:

---

## Technical Design Spec — VO-344: Stale Cache in Scheduler Configuration

### Approach

Three targeted fixes in `scheduler.py`, one new test. No schema, API surface, or frontend changes.

**1. Invert update order in `update_job_schedule()`**
Lines 254–256 mutate `_job_registry` before the APScheduler call at line 262. On APScheduler failure the exception is caught, `False` is returned, but the registry already holds the new (incorrect) config. Fix: perform the APScheduler `reschedule_job()` / `add_job()` call first; update `_job_registry` only after it succeeds.

**2. Preserve persisted triggers across restarts in `start_all_jobs()`**
Currently uses `replace_existing=True`, which clobbers any trigger stored in the SQLite jobstore with startup-code defaults. Fix: call `scheduler.get_job(job_id)` before adding; if the job already exists in APScheduler (i.e., a prior reschedule was persisted), skip `add_job()` and only sync the `enabled` state. This makes the SQLite store authoritative after the first start.

**3. Source `trigger_args` from APScheduler in read paths**
`get_all_jobs()` (line 146) and `get_job()` (line 163) already pull `trigger` from `sched_job.trigger` — good. Extend both return dicts to include structured `trigger_args` by inspecting `sched_job.trigger` fields (e.g., `sched_job.trigger.fields` for cron, `sched_job.trigger.interval` for interval) rather than `meta['trigger_args']`, eliminating the fallback to stale registry data.

---

### Files to Modify / Create

| File | Change |
|---|---|
| `backend/scheduler.py` | Fix `update_job_schedule()` (lines 249–279), `start_all_jobs()` (lines 109–131), `get_all_jobs()` / `get_job()` (lines 133–164) |
| `backend/tests/test_scheduler_race_condition.py` | Add `TestUpdateScheduleRollback` class — reschedule failure must leave registry unchanged |

No new files required.

---

### Data Model Changes

None. APScheduler's SQLite jobstore schema is unchanged.

---

### API Changes

No new endpoints. `GET /api/scheduler/jobs` and `GET /api/scheduler/jobs/<job_id>` response shape gains structured `trigger_args` (APScheduler-sourced). This is additive — no breaking change.

---

### Frontend Changes

None required. The scheduler config UI already renders whatever the API returns; the richer `trigger_args` field can be consumed opportunistically if the frontend team wants to display schedule detail, but it is not a blocker for correctness.

---

### Testing Strategy

**Existing tests** (`TestConcurrentUpdateSchedule`, `TestSchedulerRoutes`) must continue to pass — they validate the happy path and concurrency invariants.

**New regression test — `TestUpdateScheduleRollback`:**
- Mock `scheduler.reschedule_job()` to raise `Exception`
- Call `update_job_schedule()` with new trigger args
- Assert return value is `False`
- Assert `_job_registry[job_id]['trigger']` and `['trigger_args']` are **unchanged** (old values)

**Restart persistence test — `TestStartAllJobsPreservesPersistedTrigger`:**
- Register a job; call `start_all_jobs()`; call `update_job_schedule()` to change trigger
- Simulate restart by calling `start_all_jobs()` again
- Assert `scheduler.get_job(job_id).trigger` still reflects the rescheduled trigger, not the startup default
