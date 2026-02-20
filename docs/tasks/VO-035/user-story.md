# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

---

## User Story: VO-035 — Mask Sensitive Data in Log Output

**As a** platform operator deploying Virtual Office in a cloud environment,
**I want** all API keys and secrets to be masked before being written to logs,
**so that** credentials are never exposed in log aggregation tools, monitoring dashboards, or audit trails — keeping us compliant and our users' API keys safe.

---

### Acceptance Criteria

**Core fixes — `backend/core/ai_providers.py`:**
- [ ] Lines 147, 190, 237, 246: Any log statement referencing an API key, token, or credential uses a masking helper (e.g. `****<last4>`) — raw key values never appear in log output
- [ ] Exception logging does not include raw `{e}` for API call failures; only `{type(e).__name__}` or a sanitized message is used

**Core fix — `backend/core/ai_analytics.py`:**
- [ ] Line 477: Confirm no raw API key or secret appears in the log call; if `provider_config['api_key']` is referenced, it must be masked

**Root-level file cleanup:**
- [ ] `ai_providers.py` (root): Confirmed unused by any import path, then deleted
- [ ] `ai_analytics.py` (root): Confirmed unused by any import path, then deleted
- [ ] If either root-level file is actively imported somewhere, it is updated with the same masking fix before deletion is reconsidered

**Verification:**
- [ ] GitHub Code Scanning alert `py/clear-text-logging-sensitive-data` clears on re-scan (all 8 instances resolved)
- [ ] Existing tests pass; no new test failures introduced
- [ ] A `_mask_key()` (or equivalent) helper is the single canonical implementation, shared rather than duplicated

---

### Priority Reasoning

**HIGH.** These are active vulnerabilities in deployed code. API keys landing in logs means any developer, log aggregator, or SIEM tool with log access can extract user credentials. This is a data exposure risk that directly undermines trust in the platform and creates regulatory liability. Ship this before the next release.

---

### Complexity: **2 / 5**

Narrow, surgical changes. The masking pattern already exists in the codebase (`_mask_key()` is already defined). This is find-and-fix work — no architecture changes, no new dependencies. The only judgment call is confirming whether the root-level files are truly dead code before deleting them.
