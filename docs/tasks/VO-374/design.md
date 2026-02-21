# VO-374: Missing input validation in price alert notifications allows injection

## Technical Design

## VO-372: Input Validation for Price Alert Notifications — Technical Design Spec

---

### Approach

The existing code already does basic type coercion and enum-allowlisting, but has three gaps: (1) no regex constraint on `ticker` before the DB lookup, (2) no numeric bounds on `threshold`, and (3) SSE message strings are built from DB-stored values that could have been inserted before these guards existed. The fix is surgical: add validators in the API layer and add a sanitization pass on SSE payload construction. No new schema, no new libraries needed.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/api/alerts.py` | Add ticker regex + threshold bounds validation in `create_alert_endpoint()` |
| `backend/core/alert_manager.py` | Sanitize ticker/threshold values pulled from DB before building SSE payload |
| `backend/tests/test_alert_input_validation.py` | **New** — unit tests for all validation paths |

No other files require changes. SSE serialization is already safe — `send_sse_event()` in `app.py` JSON-serializes the dict rather than string-interpolating; this path is fine as-is.

---

### Data Model Changes

None. The `price_alerts` schema has no free-text fields (`ticker`, `condition_type`, `threshold`, `enabled` only). If a `name`/`notes` column is ever added, HTML sanitization would be required at that point.

---

### API Changes

`POST /api/alerts` — add two new validation gates before the existing DB lookup:

```python
# 1. Ticker format (before DB lookup)
import re
_TICKER_RE = re.compile(r'^[A-Z]{1,5}$')
ticker = data.get('ticker', '').strip().upper()
if not _TICKER_RE.match(ticker):
    return jsonify({'error': 'ticker must be 1–5 uppercase letters'}), 400

# 2. Threshold bounds
_THRESHOLD_MAX = 1_000_000
if not (0 < threshold <= _THRESHOLD_MAX):
    return jsonify({'error': f'threshold must be > 0 and ≤ {_THRESHOLD_MAX}'}), 400
```

For `pct_change` condition type, add a secondary check: `threshold <= 100` (percentage makes no sense above 100 for this UI).

No new endpoints. No breaking changes to response shape.

---

### Frontend Changes

None. Validation is server-side only. The frontend already surfaces 400 error messages from the API to the user.

---

### Testing Strategy

**File**: `backend/tests/test_alert_input_validation.py`

| Test group | Cases |
|---|---|
| `TestTickerValidation` | lowercase rejected, digits rejected, >5 chars rejected, empty rejected, symbols rejected, valid 1–5 uppercase accepted |
| `TestThresholdBounds` | zero rejected, negative rejected, above 1M rejected, non-numeric rejected, boundary values (0.01, 1M exactly) accepted |
| `TestPctChangeBounds` | >100 rejected for `pct_change` type, 100 accepted, fractional accepted |
| `TestSSEPayloadSafety` | SSE payload for a triggered alert contains only expected keys with clean values; ticker and threshold from DB are the validated-at-insert values (no extra sanitization needed once gate is in place) |
| `TestErrorResponseShape` | All 400 responses return `{'error': str}`, no raw exception text |

Reuse the existing `in_memory_db` fixture pattern from `test_price_alert_race_condition.py`. No new dependencies.
