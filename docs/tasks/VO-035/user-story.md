# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Good, I have a clear picture of the real issues. Here's the user story:

---

## User Story: Eliminate Clear-Text Logging of Sensitive Credentials

**As a** security-conscious platform operator,
**I want** all logging of AI provider API keys and sensitive response data to be masked or removed,
**so that** credentials never appear in plaintext in application logs, protecting users from credential theft via log exposure.

---

### Background

GitHub Code Scanning (HIGH severity, `py/clear-text-logging-sensitive-data`) flagged 8 instances of tainted data flow from `api_key` into `logger` calls. Root causes fall into two categories:

1. **Direct leak** — exception `str(e)` and response bodies are logged. For Google, the URL contains `?key={self.api_key}`; if requests throws a connection error, the full URL (including key) appears in `str(e)`. For Grok, `response.text` is logged verbatim and could contain token rejection details.
2. **Stale duplicate files** — root-level `ai_providers.py` and `ai_analytics.py` are older, unfixed versions of `backend/core/` equivalents. They still contain `logger.error(f"Google API error: {e}")` and `logger.error(f"Grok API error: {error_msg}")` — the versions the backend already fixed.

---

### Acceptance Criteria

**`backend/core/ai_providers.py`**
- [ ] `GrokProvider.generate_analysis` exception handler (lines 206–214): replace `logger.error(error_msg)` (where `error_msg = f"...{str(e)}"`) with `logger.error(f"Grok API error: {type(e).__name__}")`. Remove or sanitize the `error_detail` response dump (line 212) — do not log raw API response bodies.
- [ ] GitHub scanner flags at lines 147, 190, 237, 246 are resolved (verify the taint path is broken by the above change; line 190 already uses `mask_secret` correctly).

**`backend/core/ai_analytics.py`**
- [ ] Line 477–479: break the taint path from `provider_config` (which contains `api_key`) by only logging explicitly safe fields — confirm no sensitive fields from the config dict are reachable through the log call.

**Root-level duplicate files**
- [ ] Confirm `ai_providers.py` and `ai_analytics.py` at repo root are not imported by any active code path (search for imports).
- [ ] If unused: delete both files. If used by anything: apply the same masking fixes as the backend versions, then schedule a follow-up to consolidate.

**Verification**
- [ ] GitHub Code Scanning reports zero remaining `py/clear-text-logging-sensitive-data` alerts after merge.
- [ ] All existing tests pass.
- [ ] No functional behavior changes — error messages returned to callers are unchanged; only the log output is sanitized.

---

### Priority Reasoning

**P0 / Ship this sprint.** API keys in logs are a direct credential exposure vector. If logs are shipped to any observability platform (Datadog, CloudWatch, Splunk), these keys are queryable by anyone with log read access. The root-level files are particularly dangerous because they contain the pre-fix versions of code we already thought was patched. This is a compliance blocker for any SOC 2 or security audit.

---

### Complexity: 2 / 5

The fix pattern is well-understood: swap `str(e)` / `{e}` for `type(e).__name__`, remove raw response body dumps, and delete dead files. No architectural changes needed. The only risk is verifying the root-level files are truly unused before deleting.
