# VO-349: Stale cache in scheduler configuration shows outdated data

## User Story

Good — I've read enough of the scheduler code to write a grounded story. The `_job_registry` in-memory dict is the cache, and `update_job_schedule()` mutates it before the APScheduler SQLite store is updated, creating an inconsistency window. The `GET /jobs` and `GET /jobs/<id>` endpoints read from this registry, so users can see outdated config after a reschedule.

---

## User Story: Stale Cache in Scheduler Configuration

**Story**
As an admin managing job schedules, I want the scheduler configuration page to always reflect the current job settings, so that I'm not misled into thinking a schedule change took effect (or didn't) when the opposite is true.

---

**Background**

`SchedulerManager._job_registry` is an in-memory dict that acts as a cache over APScheduler's SQLite job store. `update_job_schedule()` (`scheduler.py:255`) mutates the registry _before_ calling `scheduler.reschedule_job()`. If the APScheduler call fails, the registry now holds new config while the scheduler still runs the old one — silently diverged. Conversely, on restart, the registry is rebuilt from code (`register_job()`) but the SQLite store may hold a previously-rescheduled config, so `GET /api/scheduler/jobs` shows startup defaults instead of the persisted schedule.

---

**Acceptance Criteria**

- `GET /api/scheduler/jobs` and `GET /api/scheduler/jobs/<job_id>` return schedule data sourced from APScheduler (the authoritative store), not from `_job_registry` alone
- If `scheduler.reschedule_job()` raises, `_job_registry` is **not** updated — registry and scheduler remain consistent
- After a successful `PUT /api/scheduler/jobs/<job_id>/schedule`, a subsequent `GET` on that job reflects the new trigger and schedule parameters
- After a server restart, `GET /api/scheduler/jobs` reflects the persisted APScheduler state (not just the startup-registered defaults)
- Existing scheduler tests pass; new regression test covers the "reschedule failure leaves registry unchanged" case

---

**Priority Reasoning**

**Medium-High.** This is a data-integrity bug in an admin-facing control surface. Ops staff acting on stale config could double-trigger jobs, leave misconfigured schedules in place, or incorrectly diagnose a failed reschedule as successful. The risk compounds under concurrent requests (a known issue per the recent race-condition fix in commit `80e989c`).

---

**Estimated Complexity: 2 / 5**

Scope is narrow:
1. Invert the update order in `update_job_schedule()` — reschedule in APScheduler first, update registry only on success (`scheduler.py:249–278`)
2. Refactor `get_all_jobs()` / `get_job()` to pull trigger/schedule fields live from APScheduler rather than `_job_registry` (`scheduler.py:133–164`)
3. One new unit test for the rollback-on-failure path

No schema changes, no API surface changes, no frontend work required.
