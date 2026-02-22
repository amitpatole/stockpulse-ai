# VO-405: Incorrect error handling in scheduler configuration returns 500 instead of 400

## Technical Design

Now I have everything I need. Here is the spec:

---

### 1. Approach

Extend the existing guard at `scheduler_routes.py:183` to check `isinstance(data, dict)` before checking for the `'trigger'` key, so any non-dict JSON body (array, scalar, null) is caught and returns 400 with the standard error shape. No try/except is needed — one additional condition eliminates the `AttributeError` path entirely. New test cases are added to the existing `TestTriggerBodyValidationViaHttp` class to cover each non-dict JSON type.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/scheduler_routes.py` — strengthen the body guard on line 183
- **MODIFY**: `backend/tests/test_scheduler_input_validation.py` — add cases to `TestTriggerBodyValidationViaHttp`

No other files are touched.

---

### 3. Data Model

No schema changes. This is a pure request-validation fix.

---

### 4. API Spec

No new endpoints. Corrected behaviour on existing endpoint:

**`PUT /api/scheduler/jobs/<job_id>/schedule`**

| Body type | Before fix | After fix |
|---|---|---|
| `{"trigger": "cron", ...}` (valid dict) | 200 | 200 (unchanged) |
| `{}` / missing trigger key | 400 | 400 (unchanged) |
| `["trigger"]` (array) | **500** | **400** |
| `"cron"` (string scalar) | **500** | **400** |
| `42` (number scalar) | **500** | **400** |
| `null` | 400 (falsy guard catches it) | 400 (unchanged) |

Error response shape (unchanged convention):
```json
{"success": false, "error": "Request body must include \"trigger\" (cron or interval)."}
```

---

### 5. Frontend Component Spec

Not applicable — this is a backend-only fix with no UI surface.

---

### 6. Verification

1. **Array body → 400**: `curl -X PUT .../jobs/daily_summary/schedule -H 'Content-Type: application/json' -d '["trigger"]'` must return `{"success": false, "error": "..."}` with status 400, not 500.
2. **Scalar body → 400**: repeat with `-d '"cron"'` and `-d '42'`; both must return 400.
3. **Valid dict unaffected → 200**: `curl` with `-d '{"trigger":"interval","minutes":15}'` must still return `{"success": true, ...}` with status 200 and no regression in existing `TestTriggerBodyValidationViaHttp` tests.
