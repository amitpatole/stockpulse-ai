# VO-354: Create notification sound settings in price alerts

## Technical Design

Now I have the full picture. The backend is already complete — all endpoints, the DB column, and SSE payload with `sound_type` are in place. The gap is entirely on the frontend. Here is the design spec:

---

### 1. Approach

The backend is fully implemented: `price_alerts.sound_type` column exists, all CRUD and sound-settings endpoints are live, and the SSE `alert` event already carries `sound_type`. The work is frontend-only: add missing TypeScript types and API functions, build a `PriceAlertsPanel` component with a per-alert sound picker and global settings section, fix `useSSE.ts` to resolve per-alert sound overrides, and ship the two required audio files.

---

### 2. Files to Create/Modify

- **CREATE**: `frontend/src/components/alerts/PriceAlertsPanel.tsx`
- **MODIFY**: `frontend/src/lib/types.ts` — add `PriceAlert` interface and `AlertSoundType`; fix `AlertSoundSettings.sound_type` union (`'chime' | 'beep' | 'bell'` → `'chime' | 'alarm'`)
- **MODIFY**: `frontend/src/lib/api.ts` — add `listPriceAlerts`, `createPriceAlert`, `deletePriceAlert`, `updateAlertSoundType`
- **MODIFY**: `frontend/src/hooks/useSSE.ts` — update `playAlertSound` to accept per-alert `sound_type` from the SSE event; resolve `'default'` to global setting, `'silent'` to no-op
- **MODIFY**: `frontend/src/app/settings/page.tsx` — import and render `PriceAlertsPanel`
- **CREATE**: `frontend/public/sounds/chime.mp3`
- **CREATE**: `frontend/public/sounds/alarm.mp3`

---

### 3. Data Model

Already in place. No migrations needed.

```sql
-- Existing column in price_alerts (database.py:285)
sound_type  TEXT NOT NULL DEFAULT 'default'
-- Valid values: 'default' | 'chime' | 'alarm' | 'silent'
-- Global sound settings stored in the key-value settings table
```

---

### 4. API Spec

All endpoints already exist. Summary for reference:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/alerts` | List all alerts → `PriceAlert[]` |
| `POST` | `/api/alerts` | Create alert → `{ticker, condition_type, threshold, sound_type?}` |
| `DELETE` | `/api/alerts/<id>` | Delete alert |
| `PUT` | `/api/alerts/<id>/toggle` | Enable/disable |
| `PUT` | `/api/alerts/<id>/sound` | `{sound_type}` → `{id, sound_type}` |
| `GET` | `/api/alerts/sound-settings` | Global settings |
| `PUT` | `/api/alerts/sound-settings` | Partial update of global settings |

---

### 5. Frontend Component Spec

**Component**: `PriceAlertsPanel`
**File**: `frontend/src/components/alerts/PriceAlertsPanel.tsx`
**Rendered in**: `frontend/src/app/settings/page.tsx`

**Layout — two sections:**

*Global Sound Settings card:*
- Toggle switch: "Enable alert sounds" (`enabled`)
- `<select>` labelled "Default sound": `chime` / `alarm` / `silent`
- Range input: "Volume" (0–100), aria-labelled
- Preview button: plays the selected sound immediately via Web Audio on click (satisfies browser autoplay policy)

*Alerts table:*
- Columns: **Ticker** | **Condition** | **Threshold** | **Sound** | **Status** | **Actions**
- Sound column: `<select>` with options `Default (Global) / Chime / Alarm / Silent` + icon-button to preview selection
- Status column: enabled/disabled toggle
- Actions column: delete button
- Create-alert form above the table: ticker input, condition dropdown, threshold input, sound dropdown, Submit

**Type additions to `types.ts`:**
```ts
export type AlertSoundType = 'default' | 'chime' | 'alarm' | 'silent';
export interface PriceAlert {
  id: number; ticker: string; condition_type: string;
  threshold: number; enabled: boolean;
  sound_type: AlertSoundType;
  triggered_at: string | null; created_at: string;
}
```

**`useSSE.ts` change** — `playAlertSound` receives the raw event data and resolves the sound:
```ts
function playAlertSound(settings: AlertSoundSettings, alertSoundType: AlertSoundType): void {
  if (!settings.enabled) return;
  if (settings.mute_when_active && document.hasFocus()) return;
  const resolved = alertSoundType === 'default' ? settings.sound_type : alertSoundType;
  if (resolved === 'silent') return;
  new Audio(`/sounds/${resolved}.mp3`).play().catch(() => {});
}
// Call site (line 184): playAlertSound(soundSettingsRef.current, alertEvent.sound_type ?? 'default')
```

Loading state: skeleton rows. Error state: inline error banner with retry button. Empty state: "No alerts yet" message with the create form still visible.

---

### 6. Verification

1. **Per-alert sound override**: Create two alerts — one with `chime`, one with `alarm`. Trigger both via the backend evaluation loop and confirm the browser plays the correct distinct sound for each.
2. **Global mute toggle**: In Global Sound Settings, toggle "Enable alert sounds" off. Trigger an alert; confirm no sound plays regardless of per-alert setting.
3. **Preview on picker change**: Open the sound `<select>` on any alert row, change to `alarm`, and immediately click the preview icon — confirm the alarm sound plays without needing to save, and no console errors appear for the autoplay policy path.
