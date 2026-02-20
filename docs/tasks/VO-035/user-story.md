# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Good. I have what I need. Here's the user story:

---

## User Story: VO-035 — Mask Sensitive Data in Application Logs

**As a** security-conscious operator deploying Virtual Office,
**I want** API keys and secrets to never appear in plain text in application logs,
**so that** a compromised log file or log aggregation system cannot expose credentials that grant access to paid AI provider accounts.

---

### Acceptance Criteria

**Masking in `backend/core/ai_providers.py`:**
- [ ] Lines 147, 190, 237, 246 — no API key, token, or full secret value is emitted to any logger call at any log level
- [ ] Where a key reference is useful for debugging (e.g., Grok debug log), use the existing `mask_secret()` utility from `backend.core.utils` — consistent with the fix already applied at line 189
- [ ] Error logs may include HTTP status codes and non-sensitive metadata; they must not include `response.text` if that text could reflect back secrets

**Masking in `backend/core/ai_analytics.py`:**
- [ ] Line 477 — `provider_config` dict must not be logged directly if it contains `api_key`; log only `provider_name` and `model` fields explicitly

**Root-level duplicate files:**
- [ ] `ai_providers.py` (root) — confirmed unused by import search; deleted
- [ ] `ai_analytics.py` (root) — confirmed unused by import search; deleted
- [ ] If either root file is imported anywhere, it is redirected to the `backend/core/` canonical path before deletion

**Verification:**
- [ ] GitHub Code Scanning shows zero `py/clear-text-logging-sensitive-data` alerts after merge
- [ ] Existing tests pass; no new test failures introduced
- [ ] A grep for `self.api_key` inside any `logger.*` call returns no unmasked hits across the repo

---

### Priority Reasoning

**P0 / Ship this sprint.** This is a HIGH severity finding from automated scanning — the kind that triggers compliance reviews and incident response if a log is ever exfiltrated. We already have `mask_secret()` in the codebase; this is a targeted application of an existing pattern. No design decisions needed.

---

### Complexity: 2 / 5

Surgical find-and-fix across 5 lines + deletion of 2 dead files. The `mask_secret()` helper already exists. Risk is low; blast radius is contained to logging behavior only.
