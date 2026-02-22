# VO-405: Incorrect error handling in scheduler configuration returns 500 instead of 400

## User Story

---

## User Story: Scheduler Config — 500 Instead of 400

**As a** platform engineer calling the scheduler API, **I want** malformed configuration requests to return `400 Bad Request` with a clear error message, **so that** I can diagnose client mistakes immediately rather than seeing opaque 500s that look like server failures.

---

### Root Cause

`PUT /api/scheduler/jobs/<job_id>/schedule` at `scheduler_routes.py:183–189`. The guard is:

```python
if not data or 'trigger' not in data:
    return ..., 400
trigger = data.pop('trigger')   # ← AttributeError if data is a list
```

If the body is a JSON array like `["trigger"]`, the condition passes (`'trigger' in ["trigger"]` is `True`), and `data.pop('trigger')` raises `AttributeError` — no try/except wraps it, so Flask returns 500. A single `isinstance(data, dict)` check fixes it.

---

### Acceptance Criteria

- JSON array body (e.g. `["trigger"]`) → `400`, not `500`
- JSON scalar body (e.g. `"cron"`, `42`, `null`) → `400`, not `500`
- Error shape matches existing convention: `{"success": false, "error": "..."}`
- All existing 400/200 paths unaffected — no regression
- New test cases in `TestTriggerBodyValidationViaHttp` cover each non-dict JSON type

---

### Priority Reasoning

**Medium-High.** Low blast radius, but it produces misleading 500s that pollute logs and confuse API clients into thinking there's a server fault. The fix is one line — cost-to-fix is negligible.

---

### Estimated Complexity: **1 / 5**

Single `isinstance(data, dict)` guard before `data.pop()`. New tests slot into the existing `test_scheduler_input_validation.py` class. No schema changes, no new dependencies.
