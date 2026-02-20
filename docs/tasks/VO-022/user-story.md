# VO-022: Missing input validation in alert system allows XSS

## User Story

**As a** trader using the alert system, **I want** all alert inputs (name, message body, conditions) to be sanitized before rendering, **so that** malicious scripts cannot be injected through alert fields and executed in other users' browsers.

---

## Acceptance Criteria

- All user-supplied alert fields (name, message, condition expression) are sanitized server-side before storage
- Rendered alert content is HTML-escaped on output — no raw interpolation of user data into the DOM
- Alert names and messages containing `<script>`, event handlers (e.g. `onerror=`), or other executable markup are rejected with a clear validation error
- Existing alerts with malicious content stored prior to the fix are neutralized on render (escape-on-output as a backstop)
- Unit tests cover common XSS payloads: `<script>alert(1)</script>`, `<img onerror=...>`, SVG injection
- No regression on valid alert creation with special characters (e.g. `>`, `&`, `"` in legitimate condition strings)

---

## Priority

**P1 — fix this sprint, do not ship without it.**

XSS is a direct security vulnerability. A malicious actor can craft an alert that, when viewed by another user (e.g. a shared watchlist or admin dashboard), steals session tokens or performs actions on their behalf. QA-confirmed = reproducible. Security bugs with user-data exfiltration potential are non-negotiable blockers.

---

## Complexity: 3/5

Input sanitization itself is straightforward, but alert fields are consumed in multiple rendering surfaces (UI cards, notification emails, push payloads). Each surface must be audited and hardened independently. Regression risk is moderate — overly aggressive escaping can break legitimate condition syntax. Most of the effort is in thorough test coverage across all surfaces.
