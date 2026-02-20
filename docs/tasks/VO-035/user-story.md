# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Good, I have what I need. The root-level files are diverged from `backend/core/` (different imports, different logic) — not simple duplicates. Now I'll write the story.

---

## User Story: VO-059 — Fix Clear-Text Logging of Sensitive API Keys

**As a** security-conscious platform operator,
**I want** all log output to mask API keys and tokens,
**so that** credentials are never exposed in log files, monitoring dashboards, or SIEM tools — even if those systems are compromised or accessed by unauthorized parties.

---

### Context

GitHub Code Scanning flagged 8 HIGH-severity instances of `py/clear-text-logging-sensitive-data`. The affected code logs raw or partially-exposed API keys/tokens. Specifically:

- `backend/core/ai_providers.py:190` — Grok provider logs `api_key[:10]` (CodeQL still flags prefix exposure)
- `backend/core/ai_providers.py:147` — Google API error logs full HTTP response body (may echo back key embedded in URL)
- `backend/core/ai_providers.py:246` — Exception message from provider creation may contain credential details
- `backend/core/ai_analytics.py:477` — Logs `provider_config` dict which contains a raw `api_key` field
- Root-level `ai_providers.py` and `ai_analytics.py` — Separate codepaths (not identical copies); must be audited independently

---

### Acceptance Criteria

- [ ] All logger calls that reference an API key, token, or secret use a `mask_secret()` helper that returns `****<last4>` (e.g., `****ab3f`)
- [ ] `backend/core/ai_providers.py:190` — Grok debug log uses masked key, not prefix slice
- [ ] `backend/core/ai_providers.py:147` — Google error log does **not** include raw HTTP response body verbatim; logs status code only
- [ ] `backend/core/ai_providers.py:246` — Exception string logged for provider creation errors is sanitized (no credential passthrough)
- [ ] `backend/core/ai_analytics.py:477` — `provider_config` log omits the `api_key` field entirely
- [ ] Root-level `ai_providers.py` and `ai_analytics.py` are audited: if they contain equivalent logging violations, same masking rules apply; if they are unreferenced dead code, delete them and confirm no import breaks
- [ ] `mask_secret()` helper lives in a shared utility module (not duplicated per-provider)
- [ ] All 8 CodeQL `py/clear-text-logging-sensitive-data` alerts resolve on the next scan
- [ ] No behavior change to any non-logging code paths

---

### Priority Reasoning

**P0 — ship this sprint.** HIGH severity from an automated security scanner on code that handles third-party API keys (OpenAI, Anthropic, Google, xAI). If logs are forwarded to any external system (CloudWatch, Datadog, Splunk), keys are already at risk. We're an AI company — leaking competitor API keys or customer-configured keys would be a trust-destroying incident.

---

### Estimated Complexity: **2 / 5**

The fix is mechanical: write one small `mask_secret()` utility, apply it in ~6 call sites, audit 2 root-level files for deletion eligibility. No API changes, no schema changes, no frontend impact. Risk of regression is low if the engineer doesn't touch non-logging code. Primary complexity is the root-level file audit — need to verify import graph before deleting.
