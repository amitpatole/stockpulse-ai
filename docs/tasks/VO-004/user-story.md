# VO-004: Create agent performance analytics dashboard

## User Story

## User Story: Agent Performance Analytics Dashboard

---

**User Story**

As a **platform operator**, I want a dedicated analytics dashboard showing AI agent performance metrics over time, so that I can identify underperforming agents, monitor costs, and make data-driven decisions about resource allocation.

---

**Acceptance Criteria**

- `GET /api/agents/analytics` endpoint returns:
  - [ ] Runs per day for the last 30 days, grouped by agent
  - [ ] Average duration per agent (ms)
  - [ ] Total token usage and cost per agent
  - [ ] Success rate per agent (success / total runs)
- Backend queries `agent_runs` table; response time < 500ms
- `/analytics` page renders without errors for empty data states
- **Chart 1:** Stacked `BarChart` — daily run count by agent
- **Chart 2:** `AreaChart` — cumulative cost trend over time
- **Chart 3:** `BarChart` — average response time by agent
- **Chart 4:** Donut or stacked bar — success/failure ratio per agent
- Date range picker filters all charts simultaneously (default: last 30 days)
- All charts use Tremor components; no new UI libraries introduced

---

**Priority Reasoning**

High. Without visibility into agent performance and cost, we're flying blind on one of our core product differentiators. This directly unblocks cost optimization and capacity planning conversations with customers.

---

**Estimated Complexity: 3/5**

Backend aggregation queries are straightforward if `agent_runs` is indexed on `created_at` and `agent_id`. Frontend complexity is low given Tremor's out-of-the-box chart components. Main risk: data volume at scale — add a note to paginate or limit aggregation window if table grows large.

---

## Bug Story: Race Condition in Agent Run History (Concurrent Requests)

*Found by QA during code review/testing. Blocks analytics data integrity.*

---

**User Story**

As a **platform operator**, I want agent run history to be recorded correctly under concurrent load, so that my analytics dashboard reflects accurate, complete data and I can trust the metrics I act on.

---

**Acceptance Criteria**

- [ ] Concurrent agent runs (≥ 10 simultaneous) each produce exactly one complete, non-corrupted row in `agent_runs`
- [ ] No runs are silently dropped or partially written when requests overlap
- [ ] `duration_ms`, `status`, `tokens_input`, `tokens_output`, and `estimated_cost` fields are consistent per run (no cross-contamination between concurrent rows)
- [ ] Database writes use row-level locking or a serialized write path — no bare read-modify-write sequences on shared state
- [ ] New concurrency test spins up 10 threads hitting the run-create endpoint simultaneously and asserts all 10 rows are fully written with correct data
- [ ] No regressions in `GET /api/agents/analytics` aggregate totals (counts, costs, durations) when verified against the concurrent-write fixture

---

**Priority Reasoning**

High. Corrupt or missing run records silently poison every metric on the analytics dashboard — cost, success rate, duration. Users make resource allocation decisions on this data. Fix must ship before or alongside VO-004; don't launch a dashboard built on unreliable data.

---

**Estimated Complexity: 2/5**

Root cause is almost certainly an unguarded read-modify-write or a missing transaction boundary. Fix is surgical: wrap the write path in a proper transaction (`BEGIN IMMEDIATE` for SQLite) and eliminate any shared mutable state across request threads. The concurrency regression test is the bulk of the work.
