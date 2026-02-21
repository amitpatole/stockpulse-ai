# VO-348: Race condition in price alert notifications during concurrent requests

## Technical Design

Here is the technical design spec for VO-343:

---

## VO-343 Technical Design: Price Alert Race Condition

### Approach

**Root cause**: `evaluate_price_alerts()` (`alert_manager.py:172`) runs `UPDATE ... SET enabled = 0 WHERE id = ?` — no `AND enabled = 1` in the predicate. Two threads from the `ThreadPoolExecutor(max_workers=10)` both read the same alert as `enabled=1` during the bulk SELECT (line 129), both evaluate the condition as triggered, and both succeed on the UPDATE (SQLite doesn't error; `WHERE id = ?` always matches). Both call `send_sse_event()`.

**Fix — minimal, surgical:**

1. Add `AND enabled = 1` to the UPDATE WHERE clause. SQLite's write serialization guarantees exactly one thread's UPDATE matches when `enabled = 1`; the second thread gets `rowcount = 0` because the first already flipped it.
2. Capture the cursor and gate `send_sse_event()` on `cursor.rowcount > 0`. The thread that lost the write skips notification.

No schema changes, no transaction boundary changes — `db_session()` already creates per-call connections with WAL mode, which is sufficient.

### Files to Modify/Create

| Action | Path | Change |
|--------|------|--------|
| **Modify** | `backend/core/alert_manager.py` | UPDATE predicate: `WHERE id = ? AND enabled = 1`; check `cursor.rowcount > 0` before SSE |
| **Create** | `backend/tests/test_price_alert_race_condition.py` | Concurrent regression test |

### Data Model Changes

None. `enabled`, `triggered_at`, and `idx_price_alerts_enabled (ticker, enabled)` already exist.

### API Changes

None. Internal scheduler path only; SSE event shape unchanged.

### Frontend Changes

None.

### Testing Strategy

- **Unit**: single-threaded path still triggers exactly once; already-disabled alert (`enabled=0`) produces no SSE call.
- **Concurrent regression**: 10 threads simultaneously call `evaluate_price_alerts()` on one matching alert in an in-memory SQLite DB with `send_sse_event` mocked — assert mock called **exactly once**, DB row has `enabled=0`.
- **Integration smoke**: trigger scheduler job manually, confirm no duplicate `price_alert` events in `/api/stream`.
