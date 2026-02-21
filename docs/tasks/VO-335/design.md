# VO-335: Race condition in agent run history during concurrent requests

## Technical Design

Now I have a complete picture of all three bugs. Here's the technical design spec:

---

## Technical Design Spec: Race Condition in Agent Run History

### Approach

Three surgical fixes, no schema changes, no new dependencies. The core principle: **derive `run_id` from the INSERT itself**, not from a subsequent query; and **protect shared mutable state with a per-instance lock**.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/agents/base.py` | Add `threading.Lock` to `BaseAgent`; guard state mutation; return `lastrowid` from `_persist_result` |
| `backend/api/agents.py` | Thread returned `run_id` from `run_agent`/`_persist_result`; remove `_get_latest_run_id` |
| `backend/scheduler.py` | Initialize `self._lock` in `SchedulerManager.__init__` |

---

### Fix 1 — `_persist_result` returns `lastrowid` (`backend/agents/base.py:221`)

Change `_persist_result` signature to `-> int` and replace the `conn.execute(...)` call with a cursor so `cursor.lastrowid` is accessible. Return it to the caller. `run_agent` propagates this `int` back up the call chain. The separate `_get_latest_run_id` helper in `api/agents.py` is then dead code and removed.

**Before (base.py:221–249):** `conn.execute(INSERT...)` → returns `None`

**After:** `cursor = conn.execute(INSERT...)` → `conn.commit()` → `return cursor.lastrowid`

`run_agent` (base.py:200) becomes `-> tuple[AgentResult, int]` or the `run_id` is attached to `AgentResult` as an optional field. Simpler: keep the return type as `AgentResult` and stash `run_id` as `result.metadata['run_id']`, or change `run_agent` to return `(result, run_id)` tuple. Given the API layer only unpacks these locally, a tuple return is the cleanest.

---

### Fix 2 — `BaseAgent` per-instance lock (`backend/agents/base.py:73–125`)

Add `self._lock = threading.Lock()` to `__init__`. Wrap the three state-mutating lines in `run()` (lines 98, 107–109, 123–124) in `with self._lock:` blocks — only around the assignments, not around the `execute()` call which may be long-running.

```
# Guard only the state writes, not the LLM call:
self._status = RUNNING          # lock needed here
result = self.execute(inputs)   # outside lock (long-running, IO-bound)
with self._lock:
    self._status = ...
    self._last_result = result
    self._run_count += 1
```

---

### Fix 3 — `SchedulerManager._lock` initialization (`backend/scheduler.py:42–46`)

Add `self._lock = threading.Lock()` to `SchedulerManager.__init__`, before any method that references it (`trigger_job` at line 205, `update_job_schedule` at line 239).

---

### Data Model Changes

None. No schema migration required.

---

### API Changes

No new endpoints. The `run_id` field in `POST /api/agents/<name>/run` responses (lines 367, 404 in `api/agents.py`) is corrected to use `lastrowid` rather than the `MAX(id)` query. Contract is unchanged; the value is now correct.

---

### Frontend Changes

None. The response shape is identical; only the correctness of `run_id` improves.

---

### Testing Strategy

**Unit tests** (`backend/tests/test_agents_api.py`):
- Update `test_run_id_is_returned` to assert the `run_id` comes from `_persist_result`'s return value, not from `_get_latest_run_id` (remove the mock patch on `_get_latest_run_id` — it should no longer be called)
- Add a test that `_persist_result` returns a non-zero int

**Concurrency test** (new, `backend/tests/test_agent_concurrency.py`):
- Use `threading.Thread` to fire 10 simultaneous `run_agent` calls on the same agent against an in-memory SQLite DB
- Assert all returned `run_id` values are unique and non-zero
- Assert `_run_count` on the agent instance equals 10 after all threads complete

**Regression**: Run existing `pytest backend/tests/test_agents_api.py` suite — no existing tests should fail. The mock patch on `_get_latest_run_id` in existing tests is replaced with no patch (the function is deleted).

**Manual smoke test**: Two concurrent `POST /api/agents/scanner/run` requests → both responses have distinct `run_id` values matching rows in `agent_runs`.
