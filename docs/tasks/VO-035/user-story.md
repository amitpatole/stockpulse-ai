# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

---

## User Story: VO-035 — Fix Clear-Text Logging of Sensitive Data

---

### User Story

**As a** security-conscious operator of Virtual Office,
**I want** API keys and tokens never written to logs or exposed in plain text,
**so that** a compromised log file or monitoring system cannot leak credentials that enable unauthorized access to our AI provider accounts.

---

### Context

GitHub Code Scanning flagged 8 HIGH-severity instances of `py/clear-text-logging-sensitive-data`. Investigation confirmed two categories of problems:

1. **Active vulnerabilities** in `backend/core/ai_providers.py` and `backend/core/ai_analytics.py` — logger calls and URL construction expose raw API keys/tokens.
2. **Dead code risk** — root-level `ai_providers.py` and `ai_analytics.py` are exact duplicates of the backend versions, unused, and should be deleted to eliminate the duplicate attack surface.

---

### Acceptance Criteria

**Masking in `backend/core/ai_providers.py`:**
- [ ] Line 147: Any logger call referencing an API key/token logs only a masked value (e.g., `****<last4>`)
- [ ] Line 190: Same masking applied
- [ ] Line 237: Same masking applied
- [ ] Line 246: Same masking applied — if this is a URL construction with a key query param, the key must not appear in any logged URL string

**Masking in `backend/core/ai_analytics.py`:**
- [ ] Line 477: Logger call logs only masked credential, not the raw value

**Root-level duplicate files:**
- [ ] `ai_providers.py` (root) is confirmed unused and deleted
- [ ] `ai_analytics.py` (root) is confirmed unused and deleted
- [ ] No import anywhere in the codebase references the root-level files

**Verification:**
- [ ] All 8 code scanning findings resolve (re-scan passes clean)
- [ ] Existing tests pass; no functional behavior changed
- [ ] A masked value helper (e.g., `mask_secret(value, show=4)`) is used consistently — not ad-hoc string slicing scattered across files

---

### Priority Reasoning

**Priority: P0 — Ship this sprint.**

API keys in logs are a direct credential-leak vector. If logs are forwarded to any third-party aggregator (Datadog, Splunk, CloudWatch) — which is standard practice — the keys are already exposed. This is not theoretical risk; it is a confirmed code pattern. The fix is low-risk and surgical.

---

### Estimated Complexity

**2 / 5**

The masking logic is simple (a one-liner helper). The surface area is small and well-defined (6 lines across 2 files + 2 file deletions). The main discipline required is confirming the root-level files are truly unreferenced before deleting them.
