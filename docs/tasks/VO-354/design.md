# VO-354: Create notification sound settings in price alerts

## Technical Design

Now I have everything I need. Here's the technical design spec:

---

### 1. Approach

Add a `sound_type` column to `price_alerts` for per-alert overrides, stored via a new `PUT /api/alerts/<id>/sound` endpoint. The existing SSE `alert` event payload is extended with `sound_type` so `useSSE.ts` can play the correct sound per-alert rather than the global fallback. Global sound settings (enable/volume/mute) already exist in `backend/api/alerts.py`; the settings page gets a new UI section wiring them.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/database.py` — add `_migrate_price_alerts_sound_type()` migration
- **MODIFY**: `backend/core/alert_manager.py` — `create_alert()` accepts `sound_type`; SSE payload includes `alert['sound_type']`
- **MODIFY**: `backend/api/alerts.py` — `POST /api/alerts` accepts `sound_type`; new `PUT /api/alerts/<id>/sound`; expand `_VALID_SOUND_TYPES` to `{default, chime, alarm, silent}`
- **MODIFY**: `frontend/src/lib/types.ts` — update `AlertSoundSettings.sound_type` union; add `sound_type` to `AlertEvent`; add `PriceAlert` interface
- **MODIFY**: `frontend/src/lib/api.ts` — add `updateAlertSoundType(alertId, soundType)` and `listAlerts()`
- **MODIFY**: `frontend/src/hooks/useSSE.ts` — pass per-alert `sound_type` from SSE payload to `playAlertSound()`
- **CREATE**: `frontend/src/components/alerts/PriceAlertsPanel.tsx` — alert list with inline sound picker + preview
- **MODIFY**: `frontend/src/app/settings/page.tsx` — add "Alert Sounds" global settings section + render `PriceAlertsPanel`
- **MODIFY**: `frontend/src/components/layout/Sidebar.tsx` — add Alerts nav link

---

### 3. Data Model

```sql
-- Migration: add sound_type to price_alerts
ALTER TABLE price_alerts ADD COLUMN sound_type TEXT NOT NULL DEFAULT 'default';
-- CHECK constraint enforced at application layer (Flask); SQLite ALTER TABLE doesn't support it inline
```

Global sound settings continue to use the existing `settings` key-value table (`alert_sound_enabled`, `alert_sound_type`, `alert_sound_volume`, `alert_mute_when_active`).

---

### 4. API Spec

**Existing — extend POST `/api/alerts`** (no breaking change, field is optional):
```json
// Request
{ "ticker": "AAPL", "condition_type": "price_above", "threshold": 200, "sound_type": "alarm" }
// Response 201
{ "id": 7, "ticker": "AAPL", ..., "sound_type": "alarm" }
```

**New — PUT `/api/alerts/<id>/sound`**:
```json
// Request
{ "sound_type": "chime" }   // one of: default | chime | alarm | silent
// Response 200
{ "id": 7, "sound_type": "chime" }
// Response 400: { "error": "Invalid sound_type. Must be one of: alarm, chime, default, silent" }
// Response 404: { "error": "Alert 7 not found" }
```

**SSE `alert` payload** gains `"sound_type": "alarm"` field (passed through from the alert row).

---

### 5. Frontend Component Spec

**Component**: `PriceAlertsPanel` — `frontend/src/components/alerts/PriceAlertsPanel.tsx`

**Renders in**: `frontend/src/app/settings/page.tsx` as a "Price Alerts" section (below "System Status").

**UI layout** — table with columns:

| Ticker | Condition | Threshold | Sound | Status | Actions |
|--------|-----------|-----------|-------|--------|---------|
| AAPL | price_above | $200 | `<select>` [▶ preview] | Enabled | Delete |

- Sound column: `<select>` with options `default / chime / alarm / silent`, labelled `aria-label="Sound for AAPL alert"`. Fires `PUT /api/alerts/<id>/sound` on change.
- Preview button (▶): calls `playAlertSound()` immediately with the selected type — satisfies "audition before saving" requirement.
- Loading state: skeleton rows while fetching.
- Error state: inline `<p role="alert">` banner if fetch or update fails.

**Global "Alert Sounds" section** (above `PriceAlertsPanel` in settings):
- Toggle: Enable sound notifications (maps `enabled`)
- Slider: Volume 0–100 (maps `volume`)
- Checkbox: Mute when tab is focused (maps `mute_when_active`)

All controls keyboard-navigable; sliders use `<input type="range">` with `aria-label`.

---

### 6. Verification

1. **Per-alert sound plays on trigger**: Set AAPL alert to `alarm`, trigger it in dev (manually call `evaluate_price_alerts`), verify the browser plays `alarm` not the global `chime`.
2. **Silent alert suppresses audio**: Set an alert to `silent`, trigger it, verify no sound plays even with global sounds enabled.
3. **Preview on picker change**: Select `chime` from the dropdown, click ▶ — sound plays immediately without saving the alert first.
