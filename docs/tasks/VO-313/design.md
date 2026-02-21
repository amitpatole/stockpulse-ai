# VO-313: Implement notification sound settings for price alerts

## Technical Design

Now I have enough context. Here's the spec:

---

## VO-352 Technical Design: Notification Sound Settings for Price Alerts

### Approach

Purely additive change. The existing `settings` key-value table (managed by `settings_manager.py`) absorbs the four new preference keys without schema migration. Sound playback lives entirely in the frontend SSE hook — no changes to alert evaluation logic. Two new API endpoints expose preferences. A new settings card is added to the existing settings page.

---

### Files to Modify / Create

| Action | Path |
|--------|------|
| **Modify** | `backend/api/alerts.py` — add GET/PUT `/api/alerts/sound-settings` |
| **Modify** | `frontend/src/hooks/useSSE.ts` — trigger audio on `alert` event |
| **Modify** | `frontend/src/app/settings/page.tsx` — add Alert Sound Settings card |
| **Modify** | `frontend/src/lib/api.ts` — add `getAlertSoundSettings`, `updateAlertSoundSettings` |
| **Modify** | `frontend/src/lib/types.ts` — add `AlertSoundSettings` interface |
| **Create** | `frontend/public/sounds/chime.mp3`, `bell.mp3`, `beep.mp3` |
| **Create** | `backend/tests/test_alert_sound_settings.py` |

---

### Data Model Changes

No new tables. Use the existing `settings` key-value store:

| Key | Type | Default |
|-----|------|---------|
| `alert_sound_enabled` | `"true"` / `"false"` | `"true"` |
| `alert_sound_type` | `"chime"` \| `"bell"` \| `"beep"` | `"chime"` |
| `alert_sound_volume` | `"0"`–`"100"` | `"70"` |
| `alert_mute_when_active` | `"true"` / `"false"` | `"false"` |

`settings_manager.get_setting(key, default)` already handles missing keys gracefully.

---

### API Changes

Two endpoints added to `backend/api/alerts.py` (existing blueprint, no new blueprint needed):

```
GET  /api/alerts/sound-settings
→ { enabled: bool, sound_type: str, volume: int, mute_when_active: bool }

PUT  /api/alerts/sound-settings
Body: { enabled?, sound_type?, volume?, mute_when_active? }
→ same shape, validates: sound_type ∈ {chime,bell,beep}, volume ∈ [0,100]
```

---

### Frontend Changes

**`useSSE.ts`**: In the `alert` case handler, after updating `recentAlerts`, call a `playAlertSound(settings)` utility. It reads the current settings (fetched once on mount, cached in a ref), checks `document.hasFocus()` for `mute_when_active`, then plays the appropriate `<audio>` element at the configured volume. No Web Audio API complexity needed.

**`settings/page.tsx`**: New `AlertSoundSettings` card section (parallel to existing AI provider cards) containing:
- Enable/disable toggle
- Sound selector — 3 radio/button options, each with a "Preview" button that plays the sound immediately
- Volume slider (0–100)
- "Mute when tab is active" checkbox

**`api.ts`**: `getAlertSoundSettings()` and `updateAlertSoundSettings(patch)` using the existing `request()` helper.

---

### Testing Strategy

**Backend** (`test_alert_sound_settings.py`, ~10 tests):
- GET returns all four defaults when settings table is empty
- PUT persists each field; GET reflects changes
- PUT rejects invalid `sound_type` → 400
- PUT rejects `volume` outside `[0, 100]` → 400
- Partial PUT (only `volume`) leaves other fields unchanged

**Frontend** (manual QA checklist in the PR, no unit tests for audio):
- Preview button plays sound at configured volume
- Alert SSE event triggers sound in unfocused tab
- Alert SSE event is silent with `mute_when_active=true` when tab has focus
- `enabled=false` suppresses all sounds regardless
- Settings survive page reload
