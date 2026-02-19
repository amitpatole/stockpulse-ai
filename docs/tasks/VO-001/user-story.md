# VO-001: Wire real agents into agents API (remove stubs)

## User Story

Looking at the code, this task is already shipped (commit `7d1eb49`). I'll write the user story as if it were being planned — useful for retro, documentation, and sprint history.

---

## User Story: Wire Real Agents into Agents API

**As a** dashboard user monitoring AI agent activity,
**I want** the Agents dashboard to show real execution data (actual token counts, durations, and costs),
**so that** I can trust the metrics and make informed decisions about agent usage and spend.

---

### Acceptance Criteria

- **Real dispatch**: `POST /api/agents/<name>/run` triggers the actual agent implementation in `backend/agents/` (e.g. `ScannerAgent.run()`), not a sleep-and-random-data stub
- **OpenClaw path**: If `OPENCLAW_ENABLED=true` and the bridge is reachable, execution routes through `OpenClawBridge.run_task()`; falls back to native on failure
- **Accurate metrics**: `agent_runs` DB rows contain real `tokens_input`, `tokens_output`, `duration_ms`, and `estimated_cost` sourced from the actual LLM response
- **Pre-insert pattern**: A `status='running'` row is inserted before the thread starts; it is `UPDATE`d on completion — no duplicate rows
- **SSE notification**: An `agent_status` event fires on run completion with real status/cost/duration
- **No random data**: No `random.randint`, `random.uniform`, or `time.sleep` fake simulation remains in the API layer
- **Error propagation**: If an agent raises an exception, `status='error'` and the error message are persisted to DB and returned in the SSE event
- **Existing endpoints unaffected**: `GET /api/agents`, `GET /api/agents/costs`, and `GET /api/agents/runs` continue to work and now reflect real data

---

### Priority Reasoning

**P0 — ship blocker.** Dashboard cost and token metrics were entirely fabricated. Any capacity planning, model selection, or budget decisions made using those numbers were invalid. This undermines the core value proposition of the platform.

---

### Complexity: 3 / 5

The agent implementations already existed. The work was plumbing: replacing the fake run loop with real dispatch, adding the pre-insert pattern to avoid race conditions, handling the OpenClaw fallback, and wiring SSE. No new AI logic required, but the async threading and DB update path needed care to avoid duplicate writes.
