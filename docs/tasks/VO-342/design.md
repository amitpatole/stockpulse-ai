# VO-342: Race condition in scheduler configuration during concurrent requests

## Technical Design

---

## Technical Design Spec: Race Condition in Scheduler Configuration

### 1. Approach

`SchedulerManager` (`backend/scheduler.py:47`) declares `self._lock = threading.Lock()` but **never acquires it**. Under Flask's multi-threaded WSGI server, all concurrent API requests race freely over `_job_registry`. Two concrete failure modes:

1. **Lost write** — two threads call `register_job` simultaneously; Python dict resize under concurrent assignment silently drops an entry.
2. **TOCTOU corruption** — `pause_job` reads then writes `_job_registry[job_id]` while `update_job_schedule` replaces the entry in between, leaving inconsistent state.

**Fix**: Replace `threading.Lock()` with `threading.RLock()` (reentrant, because APScheduler listener callbacks can re-enter the manager) and add `with self._lock:` guards around every `_job_registry` read/write in all eight methods. No algorithmic changes, no new state. The already-written test suite at `backend/tests/test_scheduler_race_condition.py` drives the implementation.

---

### 2. Files to Modify

| File | Change |
|---|---|
| `backend/scheduler.py` | (1) Line 47: `threading.Lock()` → `threading.RLock()`; (2) add `with self._lock:` in `register_job`, `start_all_jobs`, `get_all_jobs`, `get_job`, `pause_job`, `resume_job`, `trigger_job`, `update_job_schedule` |

`backend/api/scheduler_routes.py` — no changes needed; it delegates to `SchedulerManager` methods which will be safe after the fix.

---

### 3. Data Model Changes

None.

---

### 4. API Changes

None. All eight existing endpoints in `scheduler_routes.py` are unchanged in signature and response shape.

---

### 5. Frontend Changes

None. Backend-only thread-safety fix.

---

### 6. Testing Strategy

Run existing suite before the fix to confirm baseline failures:
```
python -m pytest backend/tests/test_scheduler_race_condition.py -v
```
`TestLockPresence::test_lock_is_created_on_init` will fail (asserts `RLock`, gets `Lock`). Concurrency tests will flake.

After the fix, all tests in `test_scheduler_race_condition.py` must pass:
- `TestConcurrentRegister` — 50 threads register distinct jobs; all 50 survive, no deadlock between concurrent writes and `get_all_jobs` reads
- `TestConcurrentPauseResume` — 5 threads toggle pause/resume 20 times each; no deadlock, `enabled` flag consistent
- `TestConcurrentUpdateSchedule` — 10 threads update the same job; final registry state is coherent
- `TestConcurrentTrigger` — 10 threads trigger the same job simultaneously; no exception or deadlock

Full regression: `python -m pytest backend/tests/ -v` must pass clean.
