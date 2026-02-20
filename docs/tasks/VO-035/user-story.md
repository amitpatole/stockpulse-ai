# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Got what I need. Here's the user story:

---

## User Story: VO-035 — Prevent Clear-Text Logging of Sensitive Data

**As a** security-conscious operator of Virtual Office,
**I want** API keys and sensitive credentials to never appear in application logs,
**so that** a compromised log file or log aggregation service cannot be used to exfiltrate live API credentials.

---

### Context

GitHub Code Scanning (CodeQL, severity: **HIGH**) flagged 8 instances of `py/clear-text-logging-sensitive-data`. The scanner traces data flow from `api_key` parameters into `logger.*` calls — either directly, or indirectly via error response bodies that may echo credentials back (e.g., `response.text` in an HTTP 4xx/5xx).

Affected:
- `backend/core/ai_providers.py` — lines 147, 190, 237, 246
- `backend/core/ai_analytics.py` — line 477
- Root-level `ai_providers.py` and `ai_analytics.py` (stale duplicates)

---

### Acceptance Criteria

**Masking (backend/core/ai_providers.py)**
- [ ] Any log statement in a function that receives `api_key` as an argument never logs the raw key value
- [ ] Where a masked key is useful for correlation (e.g., "which key was used"), log only the last 4 characters: `f"...{api_key[-4:]}"`
- [ ] `response.text` is not logged verbatim; if HTTP error body is needed for debugging, truncate to a safe length (e.g., 200 chars) with no substitution of credential values
- [ ] Lines 147, 190, 237, 246 all pass CodeQL `py/clear-text-logging-sensitive-data` with zero findings

**Masking (backend/core/ai_analytics.py)**
- [ ] Line 477 (and surrounding context) logs only the provider name, not any field sourced from `provider_config` that carries credential data
- [ ] Zero CodeQL findings on this file after the fix

**Root-level file cleanup**
- [ ] `ai_providers.py` (root) is deleted — confirmed unused by grep across all import statements
- [ ] `ai_analytics.py` (root) is deleted — confirmed unused by grep across all import statements
- [ ] No import or runtime reference to either root-level file remains in the codebase

**Regression**
- [ ] All existing tests pass after the changes
- [ ] The masking helper (if extracted as a utility) is covered by at least one unit test

---

### Priority Reasoning

**P0 — ship this sprint.** Leaked API keys in logs is a direct credential-exposure risk. If logs are shipped to any external aggregator (Datadog, CloudWatch, Splunk), or if a junior dev has read access to logs, this becomes an exfiltration vector. This is a HIGH-severity scanner finding with a trivial fix — there is no reason to defer it.

---

### Estimated Complexity

**2 / 5**

The fix is surgical: add a one-liner mask helper, substitute ~8 log calls, delete 2 files. No architectural changes, no new dependencies. The only risk is accidentally breaking an import chain if the root-level files are referenced somewhere non-obvious — hence the grep verification step in the AC.
