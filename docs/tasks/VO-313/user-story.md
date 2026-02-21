# VO-313: Implement notification sound settings for price alerts

## User Story

# User Story: Notification Sound Settings for Price Alerts

**Story ID:** VO-352
**Requested by:** Theo
**Feature Area:** Price Alerts / User Preferences

---

## User Story

As a **trader monitoring multiple price alerts**, I want to **configure notification sounds for price alert triggers**, so that **I can immediately recognize an alert firing without watching the screen**.

---

## Acceptance Criteria

- [ ] User can enable or disable notification sounds globally for price alerts
- [ ] User can select from at least 3 distinct alert sounds (e.g., chime, bell, beep)
- [ ] User can set volume level (0–100%) independently from system volume
- [ ] Sound plays immediately when a price alert SSE event is received in the browser
- [ ] Sound preference persists across sessions (stored in user preferences)
- [ ] A preview button lets users audition each sound before saving
- [ ] Sound does not play when the browser tab is in focus AND the user has a "mute when active" option enabled
- [ ] Settings are accessible from the existing Alert Settings panel
- [ ] No sound plays if notifications are globally muted by the OS/browser

---

## Priority Reasoning

**Medium priority.** Core alert triggering is already working (VO-343 resolved the race condition). Sound settings are a UX polish feature — high perceived value for active traders, low risk. Does not block any other work. Good candidate for a focused sprint task.

---

## Estimated Complexity

**2 / 5**

Primarily frontend work using the Web Audio API or preloaded audio files. Backend only needs a new user preference field. No changes to alert evaluation logic. Well-bounded scope.
