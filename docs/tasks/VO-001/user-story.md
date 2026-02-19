# VO-001: Wire real agents into agents API (remove stubs)

## User Story

Good. I have what I need.

---

## User Story: Wire Real Agents into Agents API

**Story:**
As a trader using the Virtual Office dashboard, I want agent runs to execute real AI analysis so that the cost metrics, token usage, and output I see reflect actual work done — not random numbers.

---

### Acceptance Criteria

- **Remove stubs:** `_STUB_AGENTS`, `trigger_agent_run()` stub logic, `_generate_agent_output()`, and the fake cost summary in `backend/api/agents.py` are deleted or replaced
- **Real dispatch:** `trigger_agent_run()` routes to the appropriate real agent class (`ScannerAgent`, `ResearcherAgent`, `RegimeAgent`, `InvestigatorAgent`, `DownloadTrackerAgent`) based on agent ID
- **Accurate metrics:** Token counts, duration (ms), and USD cost written to `agent_runs` table come from actual `AgentResult` objects returned by the engine — not `random.randint`/`random.uniform`
- **CrewAI path:** If `CREWAI_AVAILABLE`, runs are dispatched through `TickerPulseCrewEngine`; otherwise falls back to direct agent execution
- **OpenClaw path:** If the OpenClaw gateway is reachable, `OpenClawBridge.run_task()` is wired as an optional execution path (behind a config flag)
- **Cost summary accurate:** `get_cost_summary()` removes the "will populate once runs begin" stub and returns real aggregated data from the DB
- **SSE events:** Real run start/complete/error events fire via `send_sse_event()` with actual status
- **No regression:** Existing API contracts (request/response shapes) unchanged — only the internal execution logic changes
- **Graceful degradation:** If an agent dependency (API key missing, library not installed) fails, return a structured error in the run record rather than crashing the endpoint

---

### Priority Reasoning

**High priority.** The dashboard metrics are the core value prop — showing traders real signal. Fake data actively erodes trust. This is table-stakes functionality that should have shipped before the dashboard went live. Unblocks meaningful cost monitoring and model tuning downstream.

---

### Estimated Complexity: **3 / 5**

The real engines and agent classes already exist and are well-structured. This is primarily a wiring task — replace the stub dispatch in `agents.py` with calls into `backend/agents/`. The main risk is error handling across optional dependencies (CrewAI, OpenClaw gateway availability, missing API keys) and ensuring the SQLite writes stay consistent with the existing schema.
