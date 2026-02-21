# VO-372: Incorrect error handling in agent run history returns 500 instead of 400

## Technical Design

Now I have the full picture. The root cause is clear: line 430 is **outside** the `try/except` block.

---

## Technical Design Spec — VO-XXX: Correct Error Responses in Agent Run History

### Approach

Two-line fix with targeted validation guards added before business logic. The `int()` cast on `limit` (line 430) sits outside the `try/except`, so a non-integer value (`limit=abc`) raises an unhandled `ValueError` → Flask 500. Additionally, `status_filter` accepts arbitrary strings with no enumeration check, silently returning empty results with no diagnostic feedback. Fix both with explicit validation returning `400` before touching the DB.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/api/agents.py` | Add input validation before the `try` block in `list_recent_runs()` |
| `backend/tests/test_agents_api.py` | Add test cases for invalid `limit`, invalid `status`, and empty-string inputs |

No new files needed.

---

### Data Model Changes

None. Schema is unchanged.

---

### API Changes

**`GET /api/agents/runs`** — behaviour changes for bad input:

| Input | Before | After |
|---|---|---|
| `?limit=abc` | `500 Internal Server Error` | `400 {"error": "limit must be a positive integer"}` |
| `?status=badval` | `200` (empty results, silent) | `400 {"error": "Invalid status. Must be one of: error, running, success"}` |

Valid requests: no change.

---

### Frontend Changes

None. The frontend (`AgentRunHistory` component) already handles non-200 responses gracefully per the existing error boundary. No UI changes required.

---

### Implementation Detail

In `backend/api/agents.py`, `list_recent_runs()`:

```python
# --- Validate limit (currently unguarded int() cast causes 500) ---
raw_limit = request.args.get('limit', '50')
try:
    limit = int(raw_limit)
except ValueError:
    return jsonify({'error': 'limit must be a positive integer'}), 400
if limit <= 0:
    return jsonify({'error': 'limit must be a positive integer'}), 400
limit = min(limit, 200)

# --- Validate status against known enum ---
_VALID_STATUSES = {'running', 'success', 'error'}
status_filter = request.args.get('status')
if status_filter and status_filter not in _VALID_STATUSES:
    return jsonify({
        'error': f"Invalid status. Must be one of: {', '.join(sorted(_VALID_STATUSES))}"
    }), 400
```

This mirrors the existing pattern used in `backend/api/alerts.py:40-82` and `backend/api/scheduler_routes.py:148-161`.

---

### Testing Strategy

Extend `backend/tests/test_agents_api.py`, class `TestListRecentRuns`:

1. `test_invalid_limit_string_returns_400` — `?limit=abc` → 400, error message present
2. `test_invalid_limit_zero_returns_400` — `?limit=0` → 400
3. `test_invalid_limit_negative_returns_400` — `?limit=-5` → 400
4. `test_invalid_status_returns_400` — `?status=badval` → 400, message lists valid values
5. `test_valid_status_returns_200` — `?status=success` → 200 (regression guard)
6. `test_valid_limit_returns_200` — `?limit=10` → 200 (regression guard)

No new fixtures needed — existing `client` fixture suffices.
