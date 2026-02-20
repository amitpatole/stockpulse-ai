# VO-036: Fix code scanning: stack trace exposure in API error handlers

## Technical Design

## Technical Design Spec: VO-035 — Stack Trace Exposure Fix

---

### Approach

Mechanical find-and-replace across 4 files. The pattern is uniform: every `except Exception as e` block that returns `str(e)` in a JSON response must be changed to return a generic message while escalating logging from `logger.error()` to `logger.exception()` (which captures full traceback automatically). No architectural changes — this is purely defensive hardening at the HTTP boundary.

Two sub-patterns to fix:

1. **Direct exposure** — `'error': str(e)` or `f'AI Provider Error: {str(e)}'` in `jsonify()`
2. **Missing status codes** — `settings.py:216` returns no HTTP status alongside the exposed message

---

### Files to Modify

| File | Lines | Change |
|---|---|---|
| `backend/api/settings.py` | 213–216 | Replace `str(e)` with generic message; add `, 500` status; upgrade to `logger.exception()` |
| `backend/api/downloads.py` | 72–77, 133–138, 244–249 | Replace `str(e)` with `"An internal error occurred"` — logging already uses `logger.exception()`, no change needed there |
| `backend/api/chat.py` | 117–118, 121–122 | Replace both `f'AI Provider Error: {str(e)}'` and `f'Server Error: {str(e)}'` with generic messages; upgrade to `logger.exception()` |
| `dashboard.py` | 243, 367, 454, 458 | Same pattern — replace `str(e)` with generic messages; upgrade `logger.error()` to `logger.exception()` |

---

### Data Model Changes

None.

---

### API Changes

No new or removed endpoints. Behavior change only: error response bodies lose internal detail.

Before: `{"success": false, "error": "sqlite3.OperationalError: no such table: ai_providers"}`
After: `{"success": false, "error": "An internal error occurred"}`

HTTP status codes are preserved or corrected (missing 500 on `settings.py:216` gets added).

---

### Frontend Changes

None. Frontend already handles `success: false` responses generically — the `error` string is displayed in toasts/alerts. The message text changing to generic is acceptable UI degradation.

---

### Testing Strategy

**Unit tests** (pytest): For each patched handler, mock the dependency to raise an exception and assert:
- Response status code is 500
- Response JSON `error` field does not contain the exception class name or message text
- `logger.exception` was called (use `unittest.mock.patch`)

**Static analysis**: Re-run CodeQL locally (`codeql database analyze`) on the 4 files post-fix to confirm zero remaining `py/stack-trace-exposure` alerts.

**Smoke test**: Start the Flask app locally, trigger each endpoint in a way that causes an exception (bad DB path, invalid input), confirm the response body contains only the generic message.

No integration tests needed — logic is unchanged.
