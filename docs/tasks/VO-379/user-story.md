# VO-379: Race condition in settings persistence during concurrent requests

## User Story

# User Story: VO-350 — Race Condition in Settings Persistence

---

## User Story

**As a** trader using Virtual Office with multiple browser tabs or active API integrations,
**I want** my settings changes to be saved reliably even under concurrent requests,
**so that** my preferences are never silently lost or corrupted due to timing issues.

---

## Acceptance Criteria

- [ ] Concurrent writes to the same settings key from multiple requests result in exactly one winner — no data is silently dropped or corrupted
- [ ] Reads during an in-progress write return either the old value or the new value — never a partial/inconsistent state
- [ ] If two conflicting updates arrive simultaneously, the last-write wins deterministically (no undefined behavior)
- [ ] Settings operations are covered by a concurrency regression test with ≥10 threads hammering the same key simultaneously
- [ ] No deadlocks or starvation under sustained concurrent load (test with thread barrier pattern)
- [ ] Existing settings API response contracts are unchanged — no breaking changes to callers
- [ ] All existing settings tests continue to pass

---

## Priority Reasoning

**High.** Silent data loss in user settings is a trust-breaking bug. A user who saves preferences and sees them silently revert will question the reliability of the entire platform. This is especially acute for trading configurations (alerts, watchlists, display preferences) where stale state can affect decision-making. Pattern mirrors what we already fixed in `alert_manager.py` and `scheduler.py` — we know how to solve this.

---

## Estimated Complexity

**3 / 5**

Surgical fix — likely a missing lock, a non-atomic read-modify-write, or an absent `WHERE` clause guard (same root cause class as VO-343/VO-344). Test harness pattern is already established in the codebase. Risk is moderate only if settings persistence spans multiple tables or touches the SSE layer.

---

**Suggested assignee:** Backend engineer familiar with `alert_manager.py` / `scheduler.py` fixes.
**Spike needed?** No — investigate settings persistence module first, pattern is known.
