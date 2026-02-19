# VO-001: Wire real agents into agents API (remove stubs)

## Technical Design

## Technical Design Spec: Wire Real Agents into Agents API

---

### 1. Approach

Replace the fake run loop in `POST /api/agents/<name>/run` with real agent dispatch via the `AgentRegistry`. The core pattern: pre-insert a `status='running'` row to obtain a stable `run_id`, spin a background thread, dispatch through a OpenClaw-first/native-fallback chain, then `UPDATE` the row with real metrics from `AgentResult`. SSE notifies the frontend on completion.

---

### 2. Files to Modify/Create

| File | Action |
|---|---|
| `backend/api/agents.py` | **Modify** — gut the fake `time.sleep` + `random.*` run simulation; add `_dispatch()`, `_execute_agent_async()`, `_update_run_row()` helpers |
| `backend/agents/openclaw_engine.py` | **Reference only** — `OpenClawBridge.run_task()` already exists; no changes needed |
| `backend/agents/base.py` | **Reference only** — `AgentResult` already carries `tokens_input`, `tokens_output`, `duration_ms`, `estimated_cost` |
| `backend/agents/__init__.py` | **Reference only** — `get_registry()` singleton already present |

No new files required.

---

### 3. Data Model Changes

No schema migrations needed. The `agent_runs` table already has all required columns (`tokens_input`, `tokens_output`, `estimated_cost`, `duration_ms`, `error`, `started_at`, `completed_at`). The `_migrate_agent_runs()` path in `database.py` handles older installs that predate those columns.

The only behavioral change: `framework` column now reflects `'openclaw'` vs `'crewai'` accurately based on which dispatch path succeeded, rather than a hardcoded default.

---

### 4. API Changes

No new endpoints. Modified behavior on existing endpoint:

- `POST /api/agents/<name>/run` — now returns the pre-inserted `run_id` immediately (non-blocking), with real metrics populated asynchronously. Response shape unchanged (`{status, run_id, message}`).
- `GET /api/agents/runs` and `GET /api/agents/costs` — no contract change; now return real data rather than fabricated values.

---

### 5. Frontend Changes

None. The dashboard components consuming `/api/agents/runs` and `/api/agents/costs` were already wired to the correct endpoints and SSE event shape (`agent_status`). Real data flows in transparently.

---

### 6. Testing Strategy

**Unit tests** (`tests/test_agents_api.py`):
- Mock `AgentRegistry.get()` to return a fake agent; assert `run()` is called, not bypassed
- Assert `status='running'` row is inserted before thread starts (pre-insert pattern)
- Assert `UPDATE` is called with real `AgentResult` fields on success
- Assert `status='error'` and `error` column populated when `agent.run()` raises

**Integration tests** (`tests/integration/test_agents_integration.py`):
- Fire `POST /run` against a real SQLite test DB; poll run row until `status='completed'`; assert `tokens_input > 0` and `estimated_cost > 0`
- Test OpenClaw fallback: mock bridge as unavailable, assert native path executes

**Regression**:
- Assert no `random` or `time.sleep` imports remain in `backend/api/agents.py`
- `GET /api/agents/costs` cost values are deterministic across identical runs (not random)
