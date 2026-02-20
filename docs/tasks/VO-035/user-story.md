# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

---

## User Story: VO-035 — Prevent Clear-Text Logging of Sensitive Data

**As a** platform operator running Virtual Office in production,
**I want** all API keys and secrets to be masked before they appear in any log output,
**so that** a leaked log file cannot expose credentials that compromise our AI provider integrations or customer data.

---

### Acceptance Criteria

**Masking in `backend/core/ai_providers.py`**
- [ ] Lines 147, 190, 237, 246 — any log statement that references an API key, token, or secret uses a masked representation (last 4 chars only, e.g. `****abc1`)
- [ ] No `logger.*` call emits a raw secret value at any log level (debug, info, warning, error)
- [ ] A shared `_mask_key(value)` utility is used consistently — no ad-hoc masking inline

**Masking in `backend/core/ai_analytics.py`**
- [ ] Line 477 — confirm whether the flagged value is truly sensitive; if so, apply masking; if not, document why it is safe and suppress the scan finding
- [ ] No provider config dict containing `api_key` is logged without masking

**Root-level file cleanup**
- [ ] `ai_providers.py` (root) and `ai_analytics.py` (root) are audited: if they are unreachable dead code (no imports, no entry points), delete them
- [ ] If they are actively used, apply the same masking fixes and add a code comment explaining why they exist alongside the `backend/core/` versions
- [ ] After deletion (if applicable), confirm no tests or scripts import from the root-level paths

**Verification**
- [ ] GitHub Code Scanning reports zero `py/clear-text-logging-sensitive-data` findings on this branch after the fix
- [ ] Existing unit tests pass; add a test asserting that `_mask_key` is called (or the raw key is absent) in log output for each provider

---

### Priority Reasoning

**HIGH.** API keys in logs are a credential-exfiltration vector. Any log aggregation tool (CloudWatch, Datadog, Splunk) or a misconfigured log retention policy turns this into a standing data breach. GitHub flagged 8 HIGH-severity instances — this blocks a clean security posture and likely blocks compliance sign-off.

---

### Complexity: **2 / 5**

The masking pattern (`_mask_key`) already exists in the codebase. This is mostly find-and-fix with careful audit of the root-level files. The only judgment call is the root-level files — delete vs. fix. Low risk, contained scope.
