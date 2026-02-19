# VO-001: Wire real agents into agents API (remove stubs)

## User Story

Note: The code confirms this task is **already shipped** (commit `7d1eb49`). I'm writing the user story retrospectively to close it out properly.

---

## User Story: Wire Real Agents into Agents API

**As a** product owner reviewing the AI Agents dashboard,
**I want** the agent run metrics (tokens, duration, cost) to reflect actual execution data from real agent calls,
**so that** I can make informed decisions about agent performance, reliability, and AI spend.

---

### Acceptance Criteria

- [ ] `POST /api/agents/<name>/run` dispatches to the real agent implementation via `AgentRegistry`, not a fake simulation
- [ ] Run records in `agent_runs` DB table contain actual `tokens_input`, `tokens_output`, `duration_ms`, and `estimated_cost` from the live execution
- [ ] OpenClaw bridge is attempted first when `OPENCLAW_ENABLED=true`; native `agent.run()` is the fallback
- [ ] A pre-inserted `running` row is created before the thread starts so the UI can show in-progress state immediately
- [ ] On completion, an SSE `agent_status` event fires with real result data
- [ ] `GET /api/agents/costs` returns cost aggregates sourced from real DB rows, not random values
- [ ] No stub imports or `random` calls remain in `backend/api/agents.py`
- [ ] Existing API response shape is preserved (no frontend contract breakage)

---

### Priority Reasoning

**P0 — Blocker.** Stub data makes the entire Agents dashboard untrustworthy. Costs, run counts, and durations shown to users are fabricated, meaning any decisions based on agent ROI or performance are invalid. This undermines core product value.

---

### Complexity: 3 / 5

The agent implementations already existed in `backend/agents/`. The work was wiring the API layer to call them correctly — threading, DB row lifecycle, SSE events, and the OpenClaw/native dispatch fallback chain — without double-writing run records. Non-trivial but well-scoped.
