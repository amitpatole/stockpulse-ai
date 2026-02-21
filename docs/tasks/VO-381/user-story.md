# VO-381: Missing input validation in scheduler configuration allows injection

## User Story

# User Story: VO-379 — Input Validation in Scheduler Configuration

---

## User Story

**As a** platform administrator managing job schedules,
**I want** all scheduler configuration inputs to be validated and sanitized before processing,
**so that** malicious payloads cannot inject harmful data into the scheduler, database, or downstream systems.

---

## Acceptance Criteria

- [ ] All scheduler configuration fields (job ID, cron expressions, interval values, job parameters) are validated against a strict allowlist/schema before being processed
- [ ] Invalid or malformed inputs return a `400 Bad Request` with a descriptive error message — no partial writes occur
- [ ] Cron expressions are parsed and validated structurally (no arbitrary string passthrough to APScheduler)
- [ ] Job IDs are restricted to alphanumeric + hyphens/underscores; no special characters, SQL metacharacters, or shell operators
- [ ] Interval values are validated as positive integers within a defined min/max range
- [ ] Validation occurs at the API boundary (before any DB write or APScheduler call)
- [ ] Existing scheduler tests continue to pass; new tests cover injection payloads (SQL fragments, shell metacharacters, oversized strings)
- [ ] No change to behavior for valid inputs

---

## Priority Reasoning

**High.** This is a security vulnerability, not a UX issue. Unvalidated scheduler config inputs are a direct attack surface — malformed cron strings or injected job IDs could corrupt the schedule store, cause APScheduler errors, or (worst case) escalate to data integrity issues. Ships before next release.

---

## Estimated Complexity

**3 / 5**

Validation logic itself is straightforward. The effort is in mapping every scheduler config input, writing injection test cases, and ensuring the API boundary is the single enforcement point — not scattered across the codebase.
