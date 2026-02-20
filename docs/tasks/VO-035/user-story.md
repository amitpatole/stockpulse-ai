# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Good, I have enough context. Here's the user story:

---

## VO-038: Fix Clear-Text Logging of Sensitive Data

### User Story

**As a** security-conscious operator running Virtual Office in production,
**I want** API keys and credentials never written to log files in plain text,
**so that** a compromised log file, log aggregator, or debug output does not expose live API credentials to attackers.

---

### Acceptance Criteria

**Masking in `backend/core/ai_providers.py`:**
- [ ] Line 147: HTTP error responses logged via `logger.error` do not include raw `response.text` if it may echo back auth headers or tokens
- [ ] Line 190: Grok debug log replaces any key material with a masked version — last 4 chars only: `****{key[-4:]}`
- [ ] Line 237: Exception detail logged on unknown provider does not propagate a raw key from the exception message
- [ ] Line 246: Provider creation failure log does not include the `api_key` argument in the exception string

**Masking in `backend/core/ai_analytics.py`:**
- [ ] Line 477: Log line for provider config must not include `api_key` field — log only `provider_name` and `model`

**Shared masking utility:**
- [ ] A single `mask_secret(value: str) -> str` helper is introduced (e.g., in `backend/core/utils.py` or inline) returning `****{value[-4:]}` for strings ≥ 8 chars, `****` otherwise — reused at all call sites

**Root-level duplicate cleanup:**
- [ ] Confirm root `ai_providers.py` is not imported anywhere (it matches `backend/core/` line count exactly — likely an old copy)
- [ ] Confirm root `ai_analytics.py` is not imported anywhere (different line count — verify before deleting)
- [ ] Delete confirmed-unused root-level duplicates; if either is still imported, redirect imports to `backend/core/` and delete

**Verification:**
- [ ] `git grep -r "api_key"` on logger calls returns zero hits that log a raw key
- [ ] GitHub Code Scanning `py/clear-text-logging-sensitive-data` alerts resolve on next scan
- [ ] Existing tests pass; no functional behavior changed

---

### Priority Reasoning

**HIGH — ship this sprint.** This is a HIGH-severity CodeQL finding. API keys in logs are a first-class credential leak vector: they end up in log aggregators (Datadog, Splunk), CI output, crash reports, and `git diff`-able debug dumps. A single leaked key can compromise every OpenAI/Anthropic/Grok account tied to the app. The fix is low-risk (string masking + file deletion) with no user-facing behavior change.

---

### Complexity: **2 / 5**

Mechanical string-masking changes across ~5 call sites plus confirming and deleting unused files. No schema migrations, no API changes, no frontend impact. Risk is nearly zero — only upside.
