# VO-001: Wire real agents into agents API (remove stubs)

## Technical Design

Now I have enough context to write a precise spec. Let me put it together.

---

## VO-025 Technical Design Spec: Wire Real Agents into Agents API

### 1. Approach

The engines and persistence layer are complete. This is a **wiring task** in three parts:

1. **Replace the stub run dispatcher** in `POST /api/agents/<name>/run` — swap the fake `_simulate_run()` call with `registry.run_agent(resolved_name, inputs)` from `AgentRegistry`
2. **Bootstrap the registry** in Flask app startup so the singleton is ready before any request hits the agents blueprint
3. **Update read endpoints** (`GET /api/agents`, `GET /api/agents/costs`, `GET /api/agents/runs`) to pull live data from the DB via `AgentRegistry` methods instead of fabricating values

The OpenClaw → native fallback path already exists in `base.py`'s `run()` method. The API layer just needs to stop short-circuiting it.

---

### 2. Files to Modify / Create

| File | Change |
|---|---|
| `backend/api/agents.py` | Primary target — remove stub dispatcher, call `registry.run_agent()`, read metrics from DB |
| `backend/agents/__init__.py` | Verify `create_default_agents()` is called at app init; expose registry getter |
| `backend/app.py` | Call `create_default_agents(db_path)` during `create_app()` so registry is populated before requests |
| `backend/tests/test_agents_api.py` | Replace random-range assertions; mock `BaseAgent.execute()` or `litellm.completion` for CI |

No new files needed.

---

### 3. Data Model Changes

**None.** The `agent_runs` table schema is correct and complete. The `tokens_input`/`tokens_output` split migration already exists in `database.py`. No DDL changes required.

---

### 4. API Changes

No new endpoints. Changes are behavioral:

- **`POST /api/agents/<name>/run`**: Remove stub path. Resolve name via `AGENT_ID_MAP`, call `registry.run_agent(resolved_name, inputs)`. Return the `AgentResult` fields directly (`status`, `tokens_input`, `tokens_output`, `estimated_cost`, `duration_ms`). The registry's `_persist_result()` handles the DB write — no double-write risk since it's called inside `run_agent()`.
- **`GET /api/agents`**: Replace in-memory stub status with `registry.get_run_history()` per agent to derive last run time, real cost totals, run counts.
- **`GET /api/agents/costs`**: Replace fabricated breakdown with `registry.get_cost_summary(days=30)`.
- **`GET /api/agents/runs`**: Already queries DB in the real implementation — verify it does, no change if so.

---

### 5. Frontend Changes

**None.** The response shape from `AgentResult` matches what `AgentCard.tsx` and `page.tsx` already consume (`status`, `duration_ms`, `estimated_cost`, `tokens_input`, `tokens_output`). The `AGENT_ID_MAP` already handles the six legacy IDs → five real names.

---

### 6. Testing Strategy

**Unit tests** (`test_agents_api.py`):
- Patch `BaseAgent.execute()` to return a deterministic `AgentResult` (fixed token counts, cost, duration) — keeps tests fast, no live LLM calls
- Assert response fields match the mocked `AgentResult` exactly (not random ranges)
- Assert one row written to `agent_runs` per run call (use in-memory SQLite fixture)
- Assert all six stub IDs resolve without 404 via `AGENT_ID_MAP` parametrized test

**Integration smoke test** (manual / CI with `ANTHROPIC_API_KEY` secret):
- Single `POST /api/agents/scanner/run` against a real DB; assert `duration_ms > 0` and `tokens_output > 0`

**CI guard**: Gate live LLM tests behind `@pytest.mark.integration` and skip by default. Mock path must cover all six agent IDs.
