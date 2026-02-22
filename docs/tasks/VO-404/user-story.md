# VO-404: Incorrect error handling in news feed endpoint returns 500 instead of 400

## User Story

## User Story: VO-XXX — Correct Error Handling in News Feed Endpoint

---

### User Story

**As a** frontend developer or API consumer,
**I want** the news feed endpoint to return `400 Bad Request` for invalid input (malformed parameters, missing required fields, out-of-range values),
**so that** I can distinguish client errors from server failures and surface actionable error messages to users without triggering false alerts in error monitoring.

---

### Acceptance Criteria

- [ ] Requests with invalid or missing required parameters return `400` with a descriptive JSON error body (e.g. `{"error": "invalid parameter: 'limit' must be a positive integer"}`)
- [ ] Server-side failures (DB errors, upstream timeouts) continue to return `500`
- [ ] No `500` is returned for any input-validation failure — these are exclusively `4xx`
- [ ] Error response shape is consistent with existing API error conventions
- [ ] All new validation paths are covered by unit tests asserting the correct status code
- [ ] Existing passing tests remain green

---

### Priority Reasoning

**High.** A `500` for bad input is a correctness bug with real operational impact:
- Poisons error dashboards with noise, masking real outages
- Breaks client retry logic that gates on `5xx` vs `4xx`
- Creates a poor developer experience for anyone integrating with the API

This is a low-risk, high-clarity fix — no design decisions needed.

---

### Estimated Complexity

**2 / 5**

Input validation is localized to the endpoint handler. The fix is surgical: add/move validation before business logic, map failures to `400`. No schema changes, no cross-service impact.
