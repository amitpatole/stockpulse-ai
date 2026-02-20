# VO-007: Fix Clear-Text Logging of Sensitive Data

## User Story

**As a** security-conscious operator deploying Virtual Office,
**I want** API keys and secrets to be masked or omitted from all application logs,
**so that** credentials are never exposed in log files, monitoring systems, or crash reports — reducing the blast radius of a log compromise.

---

## Acceptance Criteria

### Masking in `backend/core/ai_providers.py`

- [ ] **Line 147** (`GoogleProvider.generate_analysis`): Any log statement containing response error text that could include auth headers is sanitized — raw `response.text` is truncated or stripped of auth tokens before logging.
- [ ] **Line 190** (`GrokProvider.generate_analysis`): The `api_key_preview` debug log is replaced with a masked version showing **last 4 chars only** — format `****<last4>` — consistent with the masking helper (see below).
- [ ] **Line 237** (`AIProviderFactory.create_provider`): Logging the `provider_name` is fine; any incidental key reference is masked.
- [ ] **Line 246** (`AIProviderFactory.create_provider`): Exception log does not include `api_key` even if the exception message contains it.

### Masking in `backend/core/ai_analytics.py`

- [ ] **Line 477**: The `provider_config` dict log is rewritten to only log `provider_name` and `model` — the `api_key` field is **never** passed into any `logger.*` call.
  ```python
  # Before (vulnerable)
  logger.info(f"Using AI provider: {provider_config['provider_name']} - {provider_config['model']}")
  # This line is actually safe on its own — confirm the scanner flags the surrounding
  # dict reference; fix whichever line leaks the key.
  ```

### Shared masking utility

- [ ] A `_mask_key(key: str) -> str` helper (or equivalent inline lambda) is introduced — returns `"****" + key[-4:]` if `len(key) >= 4`, else `"****"`. No new file needed; add it at module level in `ai_providers.py`.
- [ ] All 8 flagged sites use this helper (or equivalent inline) — no custom ad-hoc masking logic scattered across files.

### Root-level duplicate cleanup

- [ ] Confirm `ai_providers.py` (root) and `ai_analytics.py` (root) are **not imported by any production path** outside of themselves.
- [ ] If confirmed unused: **delete both root-level files**. If either is imported by a non-backend script, replace it with a thin re-export pointing to `backend/core/`.
- [ ] After deletion, verify no import errors (`python -c "from backend.core.ai_providers import AIProviderFactory"` passes).

### Verification

- [ ] GitHub Code Scanning re-run shows **0 instances** of `py/clear-text-logging-sensitive-data`.
- [ ] Existing unit tests pass (no broken imports or regressions).
- [ ] A brief manual check confirms debug logs for a provider call show `****<last4>` format, not the full key.

---

## Priority Reasoning

**HIGH — fix immediately.** This is a GitHub Code Scanning HIGH-severity finding. Leaked API keys in logs are a well-known credential exfiltration vector (OWASP A02: Cryptographic Failures). Log aggregation systems (Datadog, CloudWatch, Splunk) are commonly accessible to more people than the production environment itself. A key logged once is a key compromised. There is no upside to logging full credentials — the fix is low-risk and high-value.

---

## Estimated Complexity

**2 / 5**

Pure defensive refactor — no new features, no schema changes, no frontend impact. The main work is:
1. Add one small masking helper (~3 lines).
2. Update 8 log call sites.
3. Delete or re-export 2 root-level duplicate files.

Risk is minimal; the changes are isolated to logging statements.
