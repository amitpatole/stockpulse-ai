# VO-394: Incorrect error handling in scheduler configuration returns 500 instead of 400

## Technical Design

Confirmed. Here is the technical design spec for VO-361.

---

## VO-361 Technical Design Spec — Scheduler Config Returns 500 Instead of 400

---

### 1. Approach

The bug is a single unguarded `int()` type conversion in the `GET /api/scheduler/history` route handler (`scheduler_routes.py:228`). When a caller passes a non-integer `limit` query parameter (e.g., `?limit=abc`), `int()` raises an unhandled `ValueError` that propagates to Flask's default 500 handler. The fix wraps that conversion in a `try/except (ValueError, TypeError)` block and returns a `400` with a descriptive message — exactly the pattern used elsewhere in the validator layer. A targeted test is added to the existing scheduler test file to cover the newly-guarded path.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/scheduler_routes.py` — add `try/except` guard around `int()` on line 228
- **MODIFY**: `backend/tests/test_scheduler_race_condition.py` — add tests for the invalid `limit` parameter path (appended to existing `TestSchedulerRoutes` class)

---

### 3. Data Model

No schema changes. This is a pure API input-validation fix.

---

### 4. API Spec

Existing endpoint, corrected behavior only:

**`GET /api/scheduler/history`**

| Scenario | Status | Response Body |
|---|---|---|
| `?limit=50` (valid) | `200` | `{ "history": [...], "total": N, "filters": {...} }` |
| `?limit=abc` (non-integer) | `400` | `{ "success": false, "error": "Invalid limit: must be an integer." }` |
| `?limit=1.5` (float string) | `400` | `{ "success": false, "error": "Invalid limit: must be an integer." }` |
| DB/APScheduler failure | `500` | (unchanged — legitimate server error) |

No other endpoints change.

---

### 5. Frontend Component Spec

Not applicable. This bug is backend-only. No frontend components are affected; the history endpoint is consumed by the scheduler UI panel but no UI changes are needed — the panel already handles error responses from the API.

---

### 6. Verification

1. **Reproduces the bug before fix**: `curl "http://localhost:5000/api/scheduler/history?limit=abc"` returns `500` (confirm first, then apply fix).
2. **Validates the fix**: Same request after fix returns `400` with body `{"success": false, "error": "Invalid limit: must be an integer."}`.
3. **Regression check**: `curl "http://localhost:5000/api/scheduler/history?limit=10"` still returns `200` with a correctly filtered `history` array — valid requests are unaffected.
