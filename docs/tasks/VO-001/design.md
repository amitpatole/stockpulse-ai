# VO-001: Wire real agents into agents API (remove stubs)

## Technical Design

## Technical Design Spec: Wire Real Agents into Agents API

---

### 1. Approach

Replace the stub layer in `backend/api/agents.py` with a three-tier dispatch chain: **pre-insert → async thread → OpenClaw-or-native fallback → UPDATE row**. The key insight is separating the DB row lifecycle from execution: a `running` placeholder is written synchronously before the thread starts (giving the UI immediate feedback), then `UPDATE`d with real metrics on completion. The `AgentRegistry` singleton, already defined in `backend/agents/`, is fetched via `current_app.extensions` inside the request context.

---

### 2. Files Modified

| File | Change |
|---|---|
| `backend/api/agents.py` | Full rewrite — removed all `random` imports/calls, replaced stub `simulate_agent_run()` with `_dispatch()`, `_insert_running_row()`, `_update_run_row()`, `_execute_agent_async()` |
| `backend/agents/__init__.py` | Added `get_registry()` singleton factory with double-checked locking; no agent logic changed |
| `backend/agents/base.py` | Pre-existing — `AgentRegistry`, `AgentResult`, `AgentStatus`, `BaseAgent` already defined |

No new files created.

---

### 3. Data Model Changes

**No schema changes.** The existing `agent_runs` table already had all required columns:

```
id, agent_name, framework, status, input_data, output_data,
tokens_input, tokens_output, estimated_cost, duration_ms,
error, started_at, completed_at
```

The behavioral change: rows are now written twice — `INSERT` with `status='running'` before execution, `UPDATE` with real values after. Previously the stub did a single `INSERT` with fabricated values.

---

### 4. API Changes

**No endpoint signature changes** — contract fully preserved. Internal behavior changed:

- `POST /api/agents/<name>/run` — now dispatches via `_dispatch()` (OpenClaw → `agent_obj.run()`) instead of `simulate_agent_run()`
- `GET /api/agents/costs` — now calls `registry.get_cost_summary(days=N)` instead of computing random totals
- `GET /api/agents` and `GET /api/agents/<name>` — now enriched with real DB aggregates (`SUM(estimated_cost)`, `COUNT(*)`)

---

### 5. Frontend Changes

**None.** Response shapes are identical. The dashboard benefits automatically: real `duration_ms`, `tokens_used`, and `estimated_cost` values flow through the same JSON keys the frontend already consumes.

---

### 6. Testing Strategy

**Unit tests** — mock `AgentRegistry.get()` to return a fake agent whose `.run()` returns a controlled `AgentResult`; assert that `_update_run_row` receives the exact fields from that result.

**Integration tests** — spin up a test Flask app with an in-memory SQLite DB, call `POST /api/agents/scanner/run`, poll `GET /api/agents/runs` and assert the returned row has non-null `tokens_input`, `duration_ms`, and `estimated_cost` (not random values).

**OpenClaw fallback** — set `OPENCLAW_ENABLED=true` with a mock `OpenClawBridge.is_available()` returning `False`; verify execution falls through to native `agent_obj.run()`.

**Duplicate-write guard** — assert `agent_runs` contains exactly **one** row per trigger call (the pre-inserted row updated in-place, not two rows).
