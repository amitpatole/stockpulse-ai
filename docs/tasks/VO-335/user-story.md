# VO-335: Race condition in agent run history during concurrent requests

## User Story

Now I have a solid read of the code. Here's the user story:

---

## User Story: Race Condition in Agent Run History

**Story**

> As a **platform user monitoring agent activity**, I want **agent run history to accurately reflect each run's result when multiple agents execute concurrently**, so that **I can trust the run IDs, statuses, and cost data shown in the dashboard and API responses**.

---

**Background / Root Cause**

Three concrete race conditions found in the code:

1. **Wrong `run_id` returned under concurrency** (`api/agents.py:404`, `api/agents.py:367`): `_get_latest_run_id` uses `SELECT MAX(id)` after the INSERT. Two concurrent runs of the same agent can each read the other's `MAX(id)`, returning a mismatched run ID in the API response.

2. **Unsynchronized agent state mutation** (`agents/base.py:98-109`): `BaseAgent.run()` writes `_status`, `_last_result`, and `_run_count` on the shared agent instance with no lock. Concurrent calls corrupt these fields.

3. **Missing lock initialization in `SchedulerManager`** (`scheduler.py:205`, `scheduler.py:239`): `trigger_job` and `update_job_schedule` reference `self._lock` which is never initialized in `__init__`, causing an `AttributeError` under concurrent scheduler operations.

---

**Acceptance Criteria**

- [ ] `_persist_result` returns the new row's `id` (via `cursor.lastrowid`) so callers never need a separate `MAX(id)` query
- [ ] `_get_latest_run_id` is removed or replaced by the above; the `run_id` in the API response matches the row actually written
- [ ] `BaseAgent.run()` acquires a per-instance lock before mutating `_status`, `_last_result`, and `_run_count`
- [ ] `SchedulerManager.__init__` initializes `self._lock = threading.Lock()` before any method references it
- [ ] Concurrent POST `/api/agents/<name>/run` requests each receive their own correct `run_id` with no cross-contamination
- [ ] Existing agent run history endpoints return correct, consistent data under concurrent load
- [ ] No regression on existing agent execution or scheduling behavior

---

**Priority Reasoning**

**High.** This is a data integrity bug, not a cosmetic one. Users see wrong run IDs and stale statuses — eroding trust in the dashboard. The missing `self._lock` in `SchedulerManager` is an outright crash waiting to happen under concurrent scheduler operations. Ships soon enough to not accumulate downstream confusion.

---

**Estimated Complexity: 2 / 5**

The fixes are surgical — no schema changes, no new dependencies. Return `lastrowid` from `_persist_result`, add a `threading.Lock()` to `BaseAgent` and `SchedulerManager.__init__`, guard the state mutations. Well-scoped for a single engineer in one session.
