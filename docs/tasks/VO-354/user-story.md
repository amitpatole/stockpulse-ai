# VO-354: Create notification sound settings in price alerts

## User Story

## User Story: VO-XXX — Notification Sound Settings for Price Alerts

---

**User Story**

As a trader monitoring multiple price alerts, I want to configure notification sounds for each alert, so that I can distinguish critical alerts from routine ones without constantly watching the screen.

---

**Acceptance Criteria**

- User can enable/disable sound notifications globally in settings
- User can assign a sound type (e.g., `default`, `chime`, `alarm`, `silent`) per individual alert
- Sound plays in-browser when a price alert triggers
- Sound setting persists across sessions (stored with alert record)
- No sound plays if the browser tab is backgrounded and the browser blocks autoplay — fails silently, no error shown
- Settings UI is accessible (keyboard navigable, screen-reader labelled)
- Sound selection previews on click so user can audition before saving

---

**Priority Reasoning**

Medium. Traders with many alerts suffer from notification blindness when all alerts look identical. Sound differentiation increases reaction time on high-priority alerts — direct impact on core user value. Not blocking any critical path but meaningfully improves daily UX for power users.

---

**Estimated Complexity: 3/5**

- Frontend: sound picker UI + Web Audio API or `<audio>` playback — moderate
- Backend: one new `sound_type` column on the alerts table, migration needed
- Integration: SSE event handler already exists; just wire sound playback on receipt
- Risk: browser autoplay policies require user gesture prior to first sound — needs handling
