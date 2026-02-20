# VO-037: Price Alert System with Real-Time Notification UI

## User Story

As a **trader monitoring multiple positions**, I want to **set price alerts on tickers and get notified in real-time when conditions are triggered**, so that I can **react to market moves without watching the screen all day**.

---

## Acceptance Criteria

**Alert Builder**
- [ ] User can create an alert from any ticker context (stock grid, detail page) via a modal or inline form
- [ ] Supported condition types: price above threshold, price below threshold, percentage change from previous close (up or down)
- [ ] Threshold input validates numeric input; rejects empty or non-numeric submissions
- [ ] Created alerts appear immediately on the `/alerts` page without a page reload

**Alerts Page (`/alerts`)**
- [ ] Lists all alerts with: ticker, condition type, threshold, enabled/disabled state, last triggered timestamp (if any)
- [ ] Toggle switch enables/disables each alert individually (persisted immediately via API)
- [ ] Delete button removes an alert; no confirmation modal required (reversible via re-creation)
- [ ] Empty state shown when no alerts exist with a clear CTA to create one

**Backend — Data Model**
- [ ] `alerts` table created with columns: `id`, `ticker`, `condition_type`, `threshold`, `enabled`, `triggered_at`
- [ ] Schema migration is idempotent (safe to re-run)

**Backend — API**
- [ ] `GET /api/alerts` — returns all alerts for the session/user
- [ ] `POST /api/alerts` — creates a new alert; validates required fields; returns 400 on bad input
- [ ] `DELETE /api/alerts/:id` — deletes alert by ID; returns 404 if not found
- [ ] `PATCH /api/alerts/:id` — toggles `enabled` state

**Alert Evaluation**
- [ ] Scheduler job checks all enabled alerts on each stock data refresh cycle
- [ ] When a condition is met: set `triggered_at` to current timestamp, disable the alert, emit event to event bus
- [ ] An alert does not fire more than once without being manually re-enabled

**Real-Time Notification (SSE)**
- [ ] Browser subscribes to alert trigger events via the existing SSE/event bus connection
- [ ] Triggered alert causes a toast/banner notification with ticker and condition summary
- [ ] Bell icon in the header displays a badge count of unread triggered alerts since last page visit
- [ ] Badge clears when user visits `/alerts` or explicitly dismisses

---

## Priority Reasoning

**High priority.** Passive monitoring is a core use case for any trading tool — users can't watch the dashboard 8 hours a day. Alerts directly extend session depth and retention: users set alerts and return. The SSE infrastructure already exists, making the real-time layer low incremental cost. This is a high-ROI feature relative to its scope.

---

## Estimated Complexity

**4 / 5**

The individual pieces (CRUD API, DB table, scheduler hook, SSE push, badge UI) are each straightforward. The complexity is in the integration: the scheduler must evaluate alerts efficiently without blocking, SSE events must survive reconnects, and the frontend state must stay consistent across the alerts page and header badge. Test surface is broad.

---

**Scope cut if needed:** Ship without SSE in v1 — alerts evaluate and persist server-side, user sees triggered state by refreshing `/alerts`. Add real-time push in a fast-follow once the core alert lifecycle is solid.
