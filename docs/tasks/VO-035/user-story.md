# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Good. I have a clear picture of the issue. Here's the user story:

---

## User Story: VO-035 — Prevent Clear-Text Logging of AI Provider Credentials

**As a** security-conscious operator of Virtual Office,
**I want** API keys and secrets to never appear in plain text in application logs,
**so that** a compromised log file or log aggregation service cannot be used to steal credentials and rack up unauthorized AI provider charges.

---

### Acceptance Criteria

**Core fix — `backend/core/ai_providers.py`**
- [ ] The `mask_secret()` helper (already present at line 16) is used consistently everywhere a credential-adjacent value is logged
- [ ] Line 148: Google API key is no longer passed as a bare URL query param (`params={"key": self.api_key}`); use the `params` kwarg but ensure any debug/error logging of the request URL does not include the key in clear text
- [ ] Line 190 (Grok debug log): if API key preview is logged, it uses `mask_secret()` showing only the **last** 4 chars, not the **first** 10 (showing the beginning of a key is more dangerous than showing the end)
- [ ] Lines 237, 246 (`AIProviderFactory`): exceptions logged via `logger.error(f"... {e}")` do not inadvertently include a raw `api_key` in the exception's string representation
- [ ] No new `logger.*` call anywhere in this file logs `self.api_key`, `api_key`, or any bearer/auth token in clear text

**Core fix — `backend/core/ai_analytics.py`**
- [ ] Line 477: the flagged log statement is reviewed and confirmed not to emit a raw credential; if it does, the value is masked before logging

**Cleanup — root-level duplicates**
- [ ] `ai_providers.py` (root) is confirmed to be an unused duplicate of `backend/core/ai_providers.py` (verify no imports reference it)
- [ ] `ai_analytics.py` (root) is confirmed to be an unused duplicate of `backend/core/ai_analytics.py`
- [ ] Both root-level files are **deleted** — not just emptied — so code scanning cannot flag them again
- [ ] After deletion, `grep -r "from ai_providers import\|import ai_providers\|from ai_analytics import\|import ai_analytics"` at repo root confirms no broken imports

**Verification**
- [ ] GitHub Code Scanning shows 0 remaining `py/clear-text-logging-sensitive-data` alerts after the PR merges
- [ ] Existing tests pass; no functional behavior changes (masking is log-only)

---

### Priority Reasoning

**P0 — ship this sprint.** HIGH severity from GitHub Code Scanning on a codebase that handles multiple third-party API keys. A leaked key means unauthorized spend and potential data exposure. The root-level duplicates also create maintenance confusion — every fix has to be applied twice. Quick to fix, high risk if left open.

---

### Complexity: 2 / 5

The `mask_secret` helper already exists in `backend/core/ai_providers.py`. Work is mechanical: audit each flagged logger call, apply the helper, confirm root files are unreferenced, delete them. No architectural changes needed.
