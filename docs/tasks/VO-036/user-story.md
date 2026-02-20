# VO-036: Fix code scanning: stack trace exposure in API error handlers

## User Story

## User Story: Sanitize API Error Responses

---

**As a** security-conscious user of the Virtual Office platform,
**I want** API errors to return generic messages without internal details,
**so that** attackers cannot exploit stack traces or implementation details leaked in HTTP responses.

---

### Acceptance Criteria

- [ ] All 14 flagged instances (`settings.py`, `downloads.py`, `chat.py`, `dashboard.py`) return generic error messages (e.g., `"An internal error occurred"`) in HTTP responses — no raw exception messages, no tracebacks
- [ ] Full tracebacks are logged server-side (via `logging.exception()` or equivalent) so engineers retain debuggability
- [ ] HTTP status codes remain semantically correct (500 for server errors, 400 for bad input, etc.)
- [ ] No new stack trace exposure is introduced in surrounding code
- [ ] GitHub Code Scanning `py/stack-trace-exposure` alerts are resolved for all 14 instances

---

### Priority Reasoning

**High.** This is a MEDIUM-severity code scanning finding with 14 instances across core API files. Stack trace exposure is an [OWASP Top 10](https://owasp.org/Top10/) information disclosure risk — it hands attackers a map of our internals. Fix is low-risk and mechanical. No reason to delay.

---

### Estimated Complexity: **2 / 5**

Mechanical find-and-replace pattern across 4 files. No logic changes, no schema migrations, no frontend work. Main risk is accidentally swallowing errors without logging — which the acceptance criteria guards against.

---

**Files to touch:** `backend/api/settings.py`, `backend/api/downloads.py`, `backend/api/chat.py`, `dashboard.py`
