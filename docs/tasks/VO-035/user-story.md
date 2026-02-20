# VO-035: Fix code scanning: clear-text logging of sensitive data

## User Story

Written and saved to `docs/tasks/VO-007/user-story.md`. Here's the summary:

---

**Story:** Operators need API keys masked in all log output so a log file compromise doesn't become a credential compromise.

**Complexity: 2/5** — purely defensive, no new features, no schema or frontend changes.

**Priority: HIGH / fix now.** Code Scanning HIGH-severity finding. Logs flow into aggregators with broad access — a key logged once is a key at risk.

Key implementation callouts baked into the ACs:

- One shared `_mask_key()` helper at module level — `****<last4>` format — used by all 8 sites. No scattered ad-hoc masking.
- `ai_analytics.py` line 477 fix: log `provider_name` + `model` only, never pass the `provider_config` dict (which contains `api_key`) into any logger call.
- Root-level `ai_providers.py` and `ai_analytics.py`: confirm unused, then **delete**. If somehow imported by a non-backend script, replace with a thin re-export to `backend/core/`.
- Done condition: GitHub Code Scanning re-run returns 0 instances of `py/clear-text-logging-sensitive-data`.
