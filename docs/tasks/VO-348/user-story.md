# VO-348: Race condition in price alert notifications during concurrent requests

## User Story

Now I have enough context. Here's the user story:

---

## VO-343: Race Condition in Price Alert Notifications During Concurrent Requests

### User Story

**As a** trader who has set price alerts on watched tickers,
**I want** my alert notifications to fire exactly once when a price condition is met,
**so that** I can trust the alerts and make decisions without being confused by duplicate or missed notifications.

---

### Acceptance Criteria

- [ ] A price alert that triggers while `evaluate_price_alerts()` is being called concurrently by multiple scheduler threads fires **exactly one** SSE notification — no duplicates
- [ ] An alert that has already been disabled (triggered) is not re-evaluated or re-notified by a concurrent thread that read it as enabled before the state was written
- [ ] The `evaluate_price_alerts()` function uses a database-level check (e.g. `WHERE enabled = 1`) **within the same transaction** as the disable update, preventing TOCTOU window exploitation
- [ ] No alerts are silently dropped due to a concurrent write collision
- [ ] Duplicate SSE `price_alert` events do not appear in the client notification feed under load
- [ ] Existing unit/integration tests pass; new regression test covers the concurrent evaluation scenario

---

### Priority Reasoning

**High.** Duplicate alert notifications directly erode user trust in a trading tool where signal accuracy is the core value proposition. A trader acting on a duplicate "price above $X" notification could make an erroneous trade. The race window is real — the scheduler uses a `ThreadPoolExecutor(max_workers=10)` and the current `evaluate_price_alerts()` has a TOCTOU gap between SELECT (check enabled) and UPDATE (disable + notify).

---

### Estimated Complexity: **3 / 5**

The database schema already has the right shape (atomic `enabled = 0` update). The fix is scoped: rewrite `evaluate_price_alerts()` to use a single atomic `UPDATE ... WHERE enabled = 1 RETURNING *` pattern (or equivalent SQLite-compatible approach) so only the thread that wins the UPDATE proceeds to send the SSE event. Medium complexity because it requires careful transaction handling and a concurrent load test to verify correctness.
