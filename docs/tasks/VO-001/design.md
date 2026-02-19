# VO-001: Wire real agents into agents API (remove stubs)

## Technical Design

Now I have everything I need. Here's the technical design spec:

---

## Technical Design Spec: Wire Real Agents into Agents API

### Approach

`backend/api/agents.py` currently maintains a parallel `_STUB_AGENTS` list that bears no relationship to the real agent classes in `backend/agents/`. The fix is a **clean replacement**: initialize the `AgentRegistry` at app startup, remove the stub list, and delegate all dispatch and metadata queries to the registry.

The agent name mapping between the stub API names and real classes must be rationalized. The real agents are `scanner`, `researcher`, `regime`, `investigator`, `download_tracker` — the stubs use different names (`technical_analyst`, `sentiment_analyst`, etc.). We align on the real names throughout, since no frontend currently relies on the stub names for anything functional.

Execution path priority: **OpenClaw (if enabled and reachable)** → **CrewAI (if available)** → **direct `AgentRegistry.run_agent()`**. All three paths return an `AgentResult`; the write to `agent_runs` uses fields from that object, not `random.*`.

---

### Files to Modify / Create

| File | Change |
|------|--------|
| `backend/api/agents.py` | **Rewrite**: remove `_STUB_AGENTS`, `_find_agent()`, `_generate_agent_output()`. Replace `trigger_agent_run()` with real dispatch. Replace `get_cost_summary()` with real DB aggregation. |
| `backend/agents/__init__.py` | Expose a module-level `registry` singleton via `get_registry(db_path)` so the API and app can share the same instance. |
| `backend/app.py` | Call `create_default_agents(Config.DB_PATH)` at startup and store the returned registry on `app.extensions['agent_registry']`. |

No new files needed.

---

### Data Model Changes

None. The existing `agent_runs` schema already carries all required columns (`tokens_input`, `tokens_output`, `estimated_cost`, `duration_ms`, `framework`, `status`, `error`). The stub was writing to these columns with random data; the fix writes real `AgentResult` values instead.

---

### API Changes

**No contract changes.** Request/response shapes stay identical. Internal changes only:

- `GET /api/agents` — reads from `AgentRegistry` instead of `_STUB_AGENTS`
- `POST /api/agents/<name>/run` — dispatches real execution, returns actual `duration_ms`, `tokens_used`, `estimated_cost` from `AgentResult`
- `GET /api/agents/costs` — queries `agent_runs` table with a real `GROUP BY agent_name` aggregation instead of returning hardcoded zeros

The `status` field returned by `POST .../run` changes from `"completed"` (synchronous stub) to `"running"` → SSE event on completion, matching the existing SSE infrastructure.

---

### Frontend Changes

None required. The frontend already listens for `agent_status` SSE events and renders fields from the existing response schema. Real data will populate where zeros/randoms showed before.

---

### Testing Strategy

1. **Unit tests** (`tests/test_agents_api.py`): Mock `AgentRegistry.run_agent()` to return a fixed `AgentResult`; assert the DB write uses result fields, not random values. Assert `get_cost_summary()` returns DB-aggregated totals.

2. **Integration smoke test**: Run `ScannerAgent` directly against the test DB; verify the `agent_runs` row written has non-zero, deterministic `tokens_input`/`tokens_output` and `duration_ms > 0`.

3. **Graceful degradation test**: Patch the Anthropic API key to an invalid value; assert the run record has `status='error'` and a non-null `error` field rather than a 500.

4. **OpenClaw fallback test**: Patch `OpenClawBridge.is_available()` to return `False`; assert execution falls through to CrewAI/native path without error.
