# VO-350: Race condition in settings persistence during concurrent requests

## User Story

# User Story: VO-350 — Race Condition in Settings Persistence

---

## User Story

**As a** platform user configuring application settings,
**I want** my settings to be saved reliably even when multiple requests occur simultaneously,
**so that** my preferences are never silently corrupted or lost due to concurrent writes.

---

## Acceptance Criteria

- [ ] Concurrent settings updates from multiple requests result in a consistent final state — no data corruption or partial writes
- [ ] The last valid write wins deterministically; no phantom overwrites from stale in-flight requests
- [ ] If a concurrent write conflict is detected, the system handles it gracefully (retry or reject with clear error) — no silent data loss
- [ ] Settings reads always reflect a committed, consistent state — no dirty reads mid-write
- [ ] All existing settings endpoints return correct HTTP status codes under concurrent load
- [ ] Regression test covers ≥10 concurrent threads writing to the same settings key; final state is deterministic

---

## Priority Reasoning

**High.** Settings persistence is foundational — corrupted config silently degrades every downstream feature (alerts, scheduler, watchlists). This is a data integrity issue, not a UX polish item. Left unfixed, it undermines user trust in the platform's reliability.

---

## Complexity Estimate

**3 / 5**

Standard write-lock or optimistic concurrency pattern on the settings layer. Complexity comes from ensuring the fix is surgical (doesn't over-lock and introduce latency) and that the regression test harness is thorough. Pattern is well-established from VO-343 and VO-344.

---

**Assignee target:** Backend engineer familiar with the alert/scheduler concurrency fixes.
**Reference prior art:** `alert_manager.py` row-level locking pattern (VO-343), `scheduler.py` RLock registry (VO-344).
