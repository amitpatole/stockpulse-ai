# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

---

## User Story: VO-035 — Redact Sensitive Data from Application Logs

**As a** security-conscious operator of the Virtual Office platform,
**I want** all API keys and sensitive credentials masked before they appear in application logs,
**so that** log files, monitoring dashboards, and error tracking tools never expose secrets that could be exploited in a breach.

---

### Acceptance Criteria

- [ ] A `_mask_key(value)` utility exists (e.g., returns `****<last4>`) and is applied anywhere a credential is logged
- [ ] `backend/core/ai_providers.py` — lines 147, 190, 237, 246: no raw API key, token, or full error response detail containing credentials reaches a logger call
- [ ] `backend/core/ai_analytics.py` — line 477 area: API key values passed to provider factory are never logged in plaintext
- [ ] Exception/error log messages that may echo back provider error bodies are sanitized or truncated to prevent indirect exposure
- [ ] Root-level `ai_providers.py` and `ai_analytics.py` are **deleted** if confirmed unused (imports, test coverage, and entrypoints checked first)
- [ ] GitHub Code Scanning reports zero `py/clear-text-logging-sensitive-data` findings after the fix is merged
- [ ] No existing test coverage broken; new unit tests added for `_mask_key()` covering edge cases (None, short strings, normal keys)

---

### Priority Reasoning

**Priority: P0 — Ship this sprint.**
HIGH severity CodeQL findings in production code. Logs are routinely shipped to third-party aggregators (Datadog, Sentry, etc.). A leaked API key means unauthorized spend, data exposure, and customer trust damage. This is not debatable.

---

### Estimated Complexity: **2 / 5**

Surgical change — add a one-liner masking helper, replace a handful of f-string log calls, delete dead files. No architectural changes required. Risk of regression is low if tests are run.
