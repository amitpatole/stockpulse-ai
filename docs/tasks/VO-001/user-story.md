# VO-001: Wire real agents into agents API (remove stubs)

## User Story

Here's the user story I wrote for VO-025:

---

**User Story**

> As a **power user monitoring my AI agent fleet**, I want the agents dashboard to show real execution metrics — actual token counts, costs, and durations — so that I can make informed decisions about which agents to run and how much they're costing me.

**Key acceptance criteria:**
- `POST /api/agents/<name>/run` dispatches to the real CrewAI/OpenClaw path — no random values
- All six stub agent IDs (e.g. `sentiment_analyst`, `news_scanner`) resolve via `AGENT_ID_MAP` without 404s
- Each run persists exactly one row to `agent_runs` with a valid status and non-zero duration
- Cost/run endpoints reflect real DB data, not fabricated numbers
- OpenClaw fallback to native CrewAI works cleanly when the bridge is unavailable
- Existing tests updated to assert real response structure, not stub random ranges

**Priority: P1.** Fake metrics on a metrics dashboard is a trust killer. This is foundational correctness — has to ship before we surface the agents feature to external users.

**Complexity: 3/5.** The engines are already built (`crewai_engine.py`, `openclaw_engine.py`). This is a wiring task. Main risk is the stub-to-real name mapping, double-write prevention in DB persistence, and mocking LLM calls in CI to avoid live API costs.
