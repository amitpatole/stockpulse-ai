# VO-037: Price Alert System with Real-Time Notification UI

## Technical Design

---

## 1. Approach

The feature decomposes into four independent layers that slot into existing infrastructure with minimal disruption:

1. **New `price_alerts` table** — kept separate from the existing `alerts` table (which is a news-triggered notification log joined to `news`). Conflating them would break `/api/alerts` and `GET /api/stats`.
2. **New `backend/api/price_alerts.py` blueprint** — CRUD endpoints under `/api/price-alerts` (hyphen, not slash, avoids the naming collision cleanly).
3. **Evaluation hook inside `technical_monitor`** — the 15-min market-hours job already iterates the watchlist and has access to price data; injecting alert evaluation here is zero-cost.
4. **Frontend: `/alerts` page + bell wiring** — the Header bell icon already renders with a badge; it just needs to be wired to the new SSE event type and link to the new page.

SSE reuse: add a `price_alert_triggered` named event. `useSSE` already listens on a typed array — add the new type there and accumulate triggered alerts in a new `triggeredAlerts` slice of state. Badge clears when the user visits `/alerts` (reset via a context setter or a URL-change effect).

---

## 2. Files to Modify / Create

**Backend**
| Action | Path |
|--------|------|
| Modify | `backend/database.py` — add `price_alerts` table DDL to `_NEW_TABLES_SQL`; add `_migrate_price_alerts()` migration stub |
| Create | `backend/api/price_alerts.py` — new Blueprint, all CRUD endpoints |
| Modify | `backend/app.py` — register `price_alerts_bp` |
| Modify | `backend/jobs/technical_monitor.py` — call `evaluate_price_alerts()` after price fetch |
| Create | `backend/core/alert_evaluator.py` — pure evaluation logic, decoupled from the job |

**Frontend**
| Action | Path |
|--------|------|
| Create | `frontend/src/app/alerts/page.tsx` — `/alerts` route |
| Create | `frontend/src/components/alerts/AlertBuilder.tsx` — condition form (ticker, type, threshold) |
| Create | `frontend/src/components/alerts/AlertList.tsx` — table with enable/disable toggle + delete |
| Modify | `frontend/src/hooks/useSSE.ts` — add `price_alert_triggered` to `eventTypes`; add `triggeredAlerts` state slice |
| Modify | `frontend/src/lib/types.ts` — add `PriceAlertTriggeredEvent`, `PriceAlert` types |
| Modify | `frontend/src/lib/api.ts` — add `getAlerts()`, `createAlert()`, `deleteAlert()`, `patchAlert()` |
| Modify | `frontend/src/components/layout/Header.tsx` — bell links to `/alerts`; badge counts `triggeredAlerts`; clear on navigate |
| Modify | `frontend/src/components/layout/Sidebar.tsx` — add `/alerts` nav entry (Bell icon) |

---

## 3. Data Model Changes

New table added to `_NEW_TABLES_SQL` in `database.py`:

```sql
CREATE TABLE IF NOT EXISTS price_alerts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker         TEXT    NOT NULL,
    condition_type TEXT    NOT NULL CHECK(condition_type IN ('above','below','pct_change')),
    threshold      REAL    NOT NULL,
    enabled        INTEGER NOT NULL DEFAULT 1,
    triggered_at   TIMESTAMP,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_price_alerts_ticker  ON price_alerts(ticker);
CREATE INDEX IF NOT EXISTS idx_price_alerts_enabled ON price_alerts(enabled);
```

`condition_type` semantics:
- `above` — trigger when `last_price > threshold`
- `below` — trigger when `last_price < threshold`
- `pct_change` — trigger when `abs((last_price - prev_close) / prev_close * 100) >= threshold`

On trigger: set `enabled = 0`, `triggered_at = now()`. User must manually re-enable.

---

## 4. API Changes

New blueprint registered at `/api/price-alerts`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/price-alerts` | List all alerts; optional `?ticker=` filter |
| `POST` | `/api/price-alerts` | Create alert — body: `{ticker, condition_type, threshold}` |
| `PATCH` | `/api/price-alerts/<id>` | Toggle `enabled` (body: `{enabled: 0|1}`) |
| `DELETE` | `/api/price-alerts/<id>` | Hard-delete alert |

Validation: ticker non-empty, condition_type in enum, threshold is finite float > 0. Return `400` with `{error: "..."}` on failure, following the existing pattern in `news.py`.

---

## 5. Frontend Changes

**`/alerts` page** — two-panel layout:
- Top: `AlertBuilder` (ticker input, condition type select, threshold input, submit)
- Bottom: `AlertList` (fetches `GET /api/price-alerts` on mount; rows show ticker, condition, threshold, status badge, toggle switch, delete button)

**SSE badge wiring:**
- `useSSE` adds `triggeredAlerts: PriceAlertTriggeredEvent[]` to state, populated by `price_alert_triggered` events
- Header bell badge reads `triggeredAlerts.length`
- On navigation to `/alerts`, call a `clearTriggeredAlerts()` setter (lifted via a lightweight React context or a `useRef` flag in `useSSE`)

**Toast notification:** on `price_alert_triggered` event, render a toast (simple fixed-position div, no lib needed — existing alert-type styling in the dashboard can be copied).

---

## 6. Testing Strategy

**Backend unit tests** (`backend/tests/`)
- `test_price_alerts_api.py`: CRUD happy-paths, validation rejections (bad condition_type, non-numeric threshold, missing fields)
- `test_alert_evaluator.py`: pure function tests for `evaluate_price_alerts()` — mock a price dict, assert correct rows are triggered and disabled

**Backend integration**
- Confirm `technical_monitor` calls evaluator without error when `price_alerts` table is empty (no regression on existing job)

**Frontend (Playwright)**
- Create alert → appears in list → toggle disabled → re-enable → delete
- Navigate to `/alerts` → bell badge clears

**Key risk: scheduler thread safety** — `evaluate_price_alerts()` uses `db_session()` (its own connection, auto-committed), so no shared state with Flask request threads. Test with concurrent SSE client connected.

---

## Architecture decisions

- **`price_alerts` not `alerts`** — the existing `alerts` table is a news-notification log with a `news_id` FK; reusing it would require nullable columns and break `GET /api/stats` counts. A clean new table is the right call.
- **Evaluation in `technical_monitor`, not a new job** — it already runs every 15 min during market hours, already fetches prices, and already calls `_send_sse()`. Adding evaluation is ~20 lines with no new scheduler registration.
- **No Redux / global store** — existing SSE state lives in `useSSE`; a single new state field there is consistent. A context for badge-clear is the minimum surface needed.
- **SSE event type `price_alert_triggered`** — distinct from the existing `alert` type (news alerts), preventing badge double-counting and keeping `AlertEvent` type unchanged.
