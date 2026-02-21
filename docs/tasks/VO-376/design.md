# VO-376: Stale cache in SSE event streaming shows outdated data

## Technical Design

I have everything I need. Here's the design spec:

---

## VO-375 Technical Design Spec: Stale Cache in SSE Event Streaming

### Approach

Two independent sub-problems, fixed surgically without touching the SSE frame format.

**1. Snapshot on connect** — In `app.py:event_stream()`, after the initial heartbeat, read current state from three DB sources and push a single `snapshot` event before entering the queue loop. This is a one-time synchronous DB read per connection.

**2. TTL guard before SSE dispatch** — The concrete stale-data path is `alert_manager.py:evaluate_price_alerts()`, which reads `current_price` from `ai_ratings` at lines 130–137 with no TTL check. Add a TTL assertion before building the alert payload; include `cached_at` from `ai_ratings.updated_at` in the emitted `alert` event. For `sentiment_cache`-sourced data: propagate `updated_at` as `cached_at` wherever sentiment scores enter an SSE payload.

`technical_monitor.py` and `regime_check.py` invoke agents live — they are not a cache-staleness problem — but add `data_source: "live"` to their payloads for symmetry.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/app.py` | Add `snapshot` to `_ALLOWED_EVENT_TYPES`; emit `snapshot` event in `event_stream()` on connect |
| `backend/core/alert_manager.py` | TTL check on `ai_ratings` read; add `cached_at` to `alert` SSE payload |
| `backend/jobs/technical_monitor.py` | Add `data_source: "live"` to `technical_alerts` payload |
| `backend/jobs/regime_check.py` | Add `data_source: "live"` to `regime_update` payload |
| `frontend/src/lib/types.ts` | Add `"snapshot"` to `SSEEventType`; add `SnapshotEvent` type |
| `frontend/src/hooks/useSSE.ts` | Add `snapshot` to `eventTypes` array; add `initialSnapshot` to `SSEState`; handle in `handleEvent` switch |

**New file**: `backend/tests/test_sse_cache_staleness.py`

---

### Data Model Changes

None. `cached_at` is sourced from existing `ai_ratings.updated_at` and `sentiment_cache.updated_at` columns — no schema changes.

---

### API Changes

- `/api/stream`: emits a new `snapshot` named event immediately on connect. Payload: `{ active_alerts: [...], last_regime: {...} | null, last_technical_signal: {...} | null, timestamp }`. No breaking change — existing clients ignoring unknown event types are unaffected.

---

### Frontend Changes

- `types.ts`: add `"snapshot"` to `SSEEventType` union, add `SnapshotEvent` interface.
- `useSSE.ts`: add `"snapshot"` to `eventTypes` (line 88), add `initialSnapshot: SnapshotEvent | null` to `SSEState`, handle in `switch` block.

No new routes or components — `snapshot` populates initial state the same hook already exposes.

---

### Testing Strategy

`backend/tests/test_sse_cache_staleness.py`, three test classes:

1. **`TestSnapshotOnConnect`** — mock DB reads, call `event_stream()` generator, assert first non-heartbeat event has `type == "snapshot"` with expected keys.
2. **`TestStaleCacheTTLGuard`** — insert an `ai_ratings` row with `updated_at` older than TTL, call `evaluate_price_alerts()`, assert no `alert` SSE is emitted; repeat with fresh `updated_at`, assert SSE fires with `cached_at` field present.
3. **`TestCachedAtPropagation`** — call the price alert path with a valid cache entry, assert the `alert` payload contains `cached_at` matching `ai_ratings.updated_at`.
