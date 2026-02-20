# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

---

## User Story: VO-035 — Fix Clear-Text Logging of Sensitive Data

**As a** security-conscious operator of Virtual Office,
**I want** API keys and tokens to be masked before they appear in any log output,
**so that** secrets are never exposed in log files, monitoring dashboards, or error reports — even in the event of a breach or misconfigured log aggregator.

---

### Acceptance Criteria

- [ ] All `logger` calls in `backend/core/ai_providers.py` (lines 147, 190, 237, 246) that reference API keys or tokens log only a masked value — e.g., `****<last4>` — never the raw secret
- [ ] `backend/core/ai_analytics.py` line 477 does not log any field from `provider_config` that contains a key or token
- [ ] Root-level `ai_providers.py` and `ai_analytics.py` receive the **same masking fixes** — they are **actively imported by `dashboard.py`** and must not be deleted
- [ ] A single reusable helper (e.g., `mask_secret(value)`) is used consistently across all affected files, returning `"****" + value[-4:]`
- [ ] No raw API key, token, or secret appears in any log line under any code path (happy path or error path)
- [ ] All existing tests pass; a targeted unit test confirms `mask_secret` works correctly
- [ ] GitHub Code Scanning shows 0 remaining `py/clear-text-logging-sensitive-data` alerts

---

### Priority Reasoning

**HIGH — ship this sprint.** These are HIGH severity CodeQL findings. A leaked API key in a log file is one misconfigured S3 bucket or Datadog integration away from a full credential compromise. The fix surface is small (7 log lines across 4 files), but the blast radius of inaction is large.

**Note on root-level files:** The task description suggested deleting the root-level files as "unused duplicates." They are **not unused** — `dashboard.py` imports directly from them. Do not delete. Fix in place, and separately track consolidation of the dual file structure as tech debt.

---

### Complexity: **2 / 5**

Localized, mechanical changes. The main risk is missing a log call — the unit test closes that gap.
