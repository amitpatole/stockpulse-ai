# VO-356: Race condition in SSE event streaming during concurrent requests

## User Story

The user story and design docs are already scaffolded in the task directory. Here's the story for VO-350:

---

## VO-350: Race Condition in Settings Persistence During Concurrent Requests

---

### User Story

**As a** platform user configuring application settings,
**I want** my settings to be saved reliably even when multiple requests occur simultaneously,
**so that** my preferences are never silently corrupted or lost due to concurrent writes.

---

### Acceptance Criteria

- Concurrent settings updates from multiple requests produce a consistent final state — no partial writes or corruption
- Last valid write wins deterministically; no phantom overwrites from stale in-flight requests
- Write conflicts are handled gracefully (retry or clear rejection) — no silent data loss
- Settings reads always reflect a committed, consistent state — no dirty reads mid-write
- All existing settings endpoints return correct HTTP status codes under concurrent load
- Regression test covers ≥10 concurrent threads writing to the same settings key; final state is deterministic

---

### Priority Reasoning

**High.** Settings persistence is foundational — corrupted config silently degrades every downstream feature: alerts, scheduler, watchlists. This is a data integrity issue. Left unfixed, it erodes user trust across the whole platform.

---

### Complexity: 3 / 5

Standard module-level `RLock` pattern, same playbook as VO-343 and VO-344. Complexity is in keeping the fix surgical — don't over-lock and introduce latency. The test harness pattern is already established.

**Reference prior art:** `alert_manager.py` row-level locking (VO-343), `scheduler.py` RLock registry (VO-344).
**Target files:** `backend/core/settings_manager.py` (fix), `backend/tests/test_settings_race_condition.py` (new).
