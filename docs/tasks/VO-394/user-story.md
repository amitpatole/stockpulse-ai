# VO-394: Incorrect error handling in scheduler configuration returns 500 instead of 400

## User Story

# User Story: VO-361 — Scheduler Config Returns 500 Instead of 400

---

## User Story

**As a** developer or API consumer integrating with the Virtual Office scheduler,
**I want** invalid scheduler configuration requests to return a `400 Bad Request` with a clear error message,
**so that** I can distinguish between client-side input errors and server-side failures, and surface actionable feedback to users without triggering false alarms in error monitoring.

---

## Acceptance Criteria

- [ ] Submitting an invalid scheduler config payload (malformed fields, out-of-range values, missing required params) returns `HTTP 400` — not `500`
- [ ] The `400` response body includes a descriptive `error` field identifying what was invalid (e.g., `"invalid cron expression"`)
- [ ] Legitimate server-side failures (DB errors, APScheduler exceptions) still return `HTTP 500`
- [ ] No unhandled exceptions propagate to Flask's default 500 handler for known bad-input scenarios
- [ ] Existing passing scheduler tests remain green; new tests cover the previously-uncaught input validation paths
- [ ] No change to behavior for valid requests

---

## Priority Reasoning

**Medium-High.** This is a correctness bug with real operational impact:
- `500`s pollute error dashboards and trigger false incident alerts
- API consumers can't distinguish "my input was wrong" from "the server is broken"
- Scheduler config is a sensitive surface — miscommunication here erodes trust in the platform

Not P0 (no data loss, no crash loop), but should ship in the current sprint.

---

## Estimated Complexity

**2 / 5**

Input validation + proper HTTP status mapping is well-scoped. The fix is surgical — identify the unguarded code paths in the scheduler config handler, add validation guards, return `400` with context. The bulk of effort is writing test coverage for the new branches.
