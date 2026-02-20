# VO-003: Build price alert system with notification UI

## User Story

## User Story: Price Alert System

---

**As a** trader using the platform, **I want** to set price alerts on stocks and receive real-time notifications when conditions are met, **so that** I can act on market movements without watching charts all day.

---

### Acceptance Criteria

**Alert Management**
- User can create an alert by specifying: ticker, condition type (price above / price below / % change from close), and threshold value
- Alerts are listed on `/alerts` with active/inactive status and a toggle to enable/disable each
- User can delete an alert; deleted alerts are removed immediately from the list
- Form validates that ticker exists and threshold is a valid number before saving

**Backend / Data**
- `alerts` table exists with columns: `id`, `ticker`, `condition_type`, `threshold`, `enabled`, `triggered_at`
- `GET /api/alerts` returns all alerts for the session; `POST /api/alerts` creates one; `DELETE /api/alerts/:id` removes one
- Alert evaluation runs inside the existing scheduler job on each stock data refresh — no separate polling loop
- `triggered_at` is stamped when an alert fires; a triggered alert is auto-disabled to prevent repeat fires

**Notifications**
- Bell icon in the global header displays a badge with the count of unread triggered alerts
- When an alert triggers, the browser receives the event via SSE through the existing event bus — no page refresh needed
- Clicking the bell opens a dropdown listing recent triggers (ticker, condition, time); marking as read clears the badge

---

### Priority Reasoning

High priority. This is a core retention feature — users who set alerts have a concrete reason to return to the app daily. It also leverages infrastructure already in place (scheduler, event bus, SSE), so the marginal cost is low relative to the user value delivered.

---

### Complexity: **4 / 5**

The DB schema and REST endpoints are straightforward. Complexity comes from three intersecting pieces: wiring alert evaluation cleanly into the scheduler without degrading its performance, the SSE push path from event bus to browser, and the real-time badge/dropdown state on the frontend. Each piece is manageable, but the integration surface is non-trivial.
