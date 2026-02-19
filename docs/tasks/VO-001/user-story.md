# VO-001: Wire real agents into agents API (remove stubs)

## User Story

<<<<<<< HEAD
Note: The code confirms this task is **already shipped** (commit `7d1eb49`). I'm writing the user story retrospectively to close it out properly.
=======
Good. I have what I need.
>>>>>>> 7d1eb49 (feat: Wire real agents into agents API (remove stubs))

---

## User Story: Wire Real Agents into Agents API

<<<<<<< HEAD
**As a** product owner reviewing the AI Agents dashboard,
**I want** the agent run metrics (tokens, duration, cost) to reflect actual execution data from real agent calls,
**so that** I can make informed decisions about agent performance, reliability, and AI spend.
=======
**Story:**
As a trader using the Virtual Office dashboard, I want agent runs to execute real AI analysis so that the cost metrics, token usage, and output I see reflect actual work done — not random numbers.
>>>>>>> 7d1eb49 (feat: Wire real agents into agents API (remove stubs))

---

### Acceptance Criteria

<<<<<<< HEAD
- [ ] `POST /api/agents/<name>/run` dispatches to the real agent implementation via `AgentRegistry`, not a fake simulation
- [ ] Run records in `agent_runs` DB table contain actual `tokens_input`, `tokens_output`, `duration_ms`, and `estimated_cost` from the live execution
- [ ] OpenClaw bridge is attempted first when `OPENCLAW_ENABLED=true`; native `agent.run()` is the fallback
- [ ] A pre-inserted `running` row is created before the thread starts so the UI can show in-progress state immediately
- [ ] On completion, an SSE `agent_status` event fires with real result data
- [ ] `GET /api/agents/costs` returns cost aggregates sourced from real DB rows, not random values
- [ ] No stub imports or `random` calls remain in `backend/api/agents.py`
- [ ] Existing API response shape is preserved (no frontend contract breakage)
=======
- **Remove stubs:** `_STUB_AGENTS`, `trigger_agent_run()` stub logic, `_generate_agent_output()`, and the fake cost summary in `backend/api/agents.py` are deleted or replaced
- **Real dispatch:** `trigger_agent_run()` routes to the appropriate real agent class (`ScannerAgent`, `ResearcherAgent`, `RegimeAgent`, `InvestigatorAgent`, `DownloadTrackerAgent`) based on agent ID
- **Accurate metrics:** Token counts, duration (ms), and USD cost written to `agent_runs` table come from actual `AgentResult` objects returned by the engine — not `random.randint`/`random.uniform`
- **CrewAI path:** If `CREWAI_AVAILABLE`, runs are dispatched through `TickerPulseCrewEngine`; otherwise falls back to direct agent execution
- **OpenClaw path:** If the OpenClaw gateway is reachable, `OpenClawBridge.run_task()` is wired as an optional execution path (behind a config flag)
- **Cost summary accurate:** `get_cost_summary()` removes the "will populate once runs begin" stub and returns real aggregated data from the DB
- **SSE events:** Real run start/complete/error events fire via `send_sse_event()` with actual status
- **No regression:** Existing API contracts (request/response shapes) unchanged — only the internal execution logic changes
- **Graceful degradation:** If an agent dependency (API key missing, library not installed) fails, return a structured error in the run record rather than crashing the endpoint
>>>>>>> 7d1eb49 (feat: Wire real agents into agents API (remove stubs))

---

### Priority Reasoning

<<<<<<< HEAD
**P0 — Blocker.** Stub data makes the entire Agents dashboard untrustworthy. Costs, run counts, and durations shown to users are fabricated, meaning any decisions based on agent ROI or performance are invalid. This undermines core product value.

---

### Complexity: 3 / 5

The agent implementations already existed in `backend/agents/`. The work was wiring the API layer to call them correctly — threading, DB row lifecycle, SSE events, and the OpenClaw/native dispatch fallback chain — without double-writing run records. Non-trivial but well-scoped.
=======
**High priority.** The dashboard metrics are the core value prop — showing traders real signal. Fake data actively erodes trust. This is table-stakes functionality that should have shipped before the dashboard went live. Unblocks meaningful cost monitoring and model tuning downstream.

---

### Estimated Complexity: **3 / 5**

The real engines and agent classes already exist and are well-structured. This is primarily a wiring task — replace the stub dispatch in `agents.py` with calls into `backend/agents/`. The main risk is error handling across optional dependencies (CrewAI, OpenClaw gateway availability, missing API keys) and ensuring the SQLite writes stay consistent with the existing schema.
>>>>>>> 7d1eb49 (feat: Wire real agents into agents API (remove stubs))
