# VO-367: Missing input validation in SSE event streaming allows injection

## Technical Design

## VO-350 Technical Design Spec: SSE Input Validation

---

### Approach

Single-point hardening at `send_sse_event` in `backend/app.py`. All SSE emission flows through this function (directly or via `_helpers.py:_send_sse`), so one validation gate covers all 10+ callers without touching each callsite. The stream endpoint's f-string interpolation of `event_type` is the primary injection surface — a newline in that field breaks SSE framing and injects rogue events.

**Three-step guard inside `send_sse_event`:**
1. Validate `event_type` against an allowlist of known event names (alphanumeric + hyphens, max 64 chars).
2. Reject or truncate oversized payloads (configurable cap, e.g. 64 KB serialized).
3. Wrap `json.dumps` in try/except — log and drop on serialization failure.

The `data` dict body is safe from SSE-frame injection via `json.dumps` (newlines are encoded as `\n`), but oversized or non-serializable payloads must be caught server-side rather than surfaced to clients.

---

### Files to Modify / Create

| File | Action | Change |
|---|---|---|
| `backend/app.py` | Modify | Harden `send_sse_event` with validation logic |
| `backend/tests/test_sse_validation.py` | Create | Unit tests for the new guard |

No other files need changes — all callers go through `send_sse_event`.

---

### Data Model Changes

None. No new DB tables or columns.

---

### API Changes

None. `/api/stream` endpoint behavior is unchanged for valid payloads. Invalid payloads are silently dropped server-side with an error log — the SSE stream stays open.

---

### Frontend Changes

None. Valid events continue to arrive unchanged. Frontend never sees rejected payloads.

---

### Implementation Detail (backend/app.py)

```python
_ALLOWED_EVENT_TYPES = frozenset({
    'heartbeat', 'alert', 'provider_fallback', 'job_completed',
    'technical_alerts', 'regime_update', 'morning_briefing',
    'daily_summary', 'weekly_review', 'reddit_trending', 'download_tracker',
})
_MAX_PAYLOAD_BYTES = 65_536  # 64 KB

def send_sse_event(event_type: str, data: dict) -> None:
    if event_type not in _ALLOWED_EVENT_TYPES:
        logger.error("SSE blocked: unknown event_type %r", event_type)
        return
    try:
        serialized = json.dumps(data)
    except (TypeError, ValueError) as exc:
        logger.error("SSE blocked: non-serializable payload for %r: %s", event_type, exc)
        return
    if len(serialized.encode()) > _MAX_PAYLOAD_BYTES:
        logger.error("SSE blocked: payload for %r exceeds %d bytes", event_type, _MAX_PAYLOAD_BYTES)
        return
    # existing queue-push logic unchanged ...
```

---

### Testing Strategy

New file `backend/tests/test_sse_validation.py`, patching `send_sse_event`'s internal queue to observe what gets enqueued:

| Test | Scenario |
|---|---|
| `test_valid_event_passes_through` | Known event type + clean dict reaches client queues |
| `test_unknown_event_type_blocked` | Unknown string → dropped, error logged, no queue push |
| `test_newline_in_event_type_blocked` | `"alert\ndata: injected"` → blocked by allowlist |
| `test_oversized_payload_dropped` | String field >64 KB → blocked, error logged |
| `test_non_serializable_payload_dropped` | Payload with non-JSON type (e.g. `set`) → blocked |
| `test_existing_callers_unaffected` | All 10 real event types in allowlist pass through |

All tests use `unittest.mock.patch` consistent with existing patterns in `test_price_alert_race_condition.py`.
