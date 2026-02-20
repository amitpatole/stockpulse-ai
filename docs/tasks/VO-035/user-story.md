# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Good. I have everything I need. Here's the user story:

---

## User Story: VO-035 — Mask Sensitive Data in Application Logs

**As a** security-conscious operator deploying Virtual Office,
**I want** API keys and tokens to never appear in plain text in application logs,
**so that** a compromised log file or log aggregation system cannot expose credentials that control our AI provider spend.

---

### Context

GitHub Code Scanning (CodeQL) flagged 8 HIGH-severity instances of `py/clear-text-logging-sensitive-data`. The root cause is two-fold:

1. **Google provider** embeds `self.api_key` directly in a URL query string (`?key={api_key}`). If that request fails, `logger.error(f"Google API error: {e}")` logs the full exception — which includes the URL with the raw key.
2. **Factory & analytics** pass `api_key` through code paths where exceptions could surface the raw value in log output.
3. **Root-level duplicates** (`ai_providers.py`, `ai_analytics.py`) replicate the same vulnerabilities and are still imported by `dashboard.py` — so both copies must be fixed.

---

### Acceptance Criteria

**Google Provider fix (backend/core/ai_providers.py ~line 145)**
- [ ] API key is moved from the URL query string to a request header (e.g., `x-goog-api-key`) so it never appears in the request URL
- [ ] `logger.error` calls in the Google provider exception handler cannot transitively expose the raw key via exception message (URL is no longer the leak vector)

**Consistent masking across all providers (backend/core/ai_providers.py)**
- [ ] Any `logger.*` call that references `api_key`, `self.api_key`, or a variable derived from them uses `mask_secret()` (already defined in the file — last 4 chars only)
- [ ] Lines ~147, 190, 237, 246 (CodeQL-flagged) are confirmed clean after fix — either no log call touches the key, or `mask_secret()` is applied

**Analytics logger safety (backend/core/ai_analytics.py ~line 477)**
- [ ] `provider_config` dict is never logged in full; any diagnostic log that references provider config only logs `provider_name` and `model`, never `api_key`

**Root-level file cleanup**
- [ ] `ai_providers.py` (root): determine if `dashboard.py` still imports it directly; if yes, apply the same masking fixes; if it can be safely deleted (imports refactored to `backend.core`), delete it
- [ ] `ai_analytics.py` (root): same determination — fix or delete; do not leave a vulnerable duplicate
- [ ] No import errors introduced: `dashboard.py` and any other callers resolve correctly after the change

**Verification**
- [ ] GitHub Code Scanning reports zero remaining `py/clear-text-logging-sensitive-data` findings in these files
- [ ] Existing test suite passes (no regressions)
- [ ] A grep for `logger.*api_key` and `logger.*token` in affected files returns only masked calls

---

### Priority Reasoning

**P1 — ship this sprint.** API keys in logs are a direct credential leak path. A single log aggregation breach (Datadog, Splunk, CloudWatch) hands an attacker unlimited AI API spend. GitHub has already flagged it as HIGH. The fix is low-risk and surgical.

---

### Complexity: **2 / 5**

The `mask_secret()` helper already exists. The Google URL-to-header change is a 2-line swap. The root-level file decision adds a small investigation step but the actual code change is mechanical. No schema changes, no new dependencies.
