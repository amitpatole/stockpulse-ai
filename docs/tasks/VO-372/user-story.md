# VO-372: Incorrect error handling in agent run history returns 500 instead of 400

## User Story

# User Story: VO-XXX — Correct Error Responses in Agent Run History

---

## User Story

**As a** developer or API consumer integrating with the agent run history endpoint,
**I want** the API to return a `400 Bad Request` when I submit invalid input,
**so that** I can distinguish my own mistakes from server-side failures and debug integrations quickly.

---

## Acceptance Criteria

- [ ] Submitting a malformed or missing required parameter to the agent run history endpoint returns `400`, not `500`
- [ ] The `400` response includes a clear, human-readable error message describing what was invalid
- [ ] Valid requests continue to return `200` with correct data — no regression
- [ ] Server logs do not record a 500-level error for client-caused bad input
- [ ] Any related input validation is applied consistently across all agent run history routes (GET/POST as applicable)

---

## Priority Reasoning

**High.** A `500` on bad input:
1. Misleads consumers into thinking the server is broken when the fault is theirs
2. Pollutes error monitoring with false alerts (Sentry/Datadog noise)
3. Signals missing input validation — a potential attack surface

This is a correctness bug with low blast radius but high signal-to-noise cost.

---

## Estimated Complexity

**2 / 5** — Localized fix. Identify the endpoint handler, add input validation before business logic, return `400` with message. Likely 1–2 files touched. Add or extend existing test coverage for the error path.
