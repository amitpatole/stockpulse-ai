# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

---

## VO-035 Technical Design Spec

**Approach:** Three changes in dependency order — sanitize logger calls, confirm the `ai_analytics.py` alert is a false positive, then migrate `dashboard.py` imports and delete root-level duplicates.

---

### Root cause

`mask_secret()` already exists at `backend/core/ai_providers.py:16`. The issue is that it isn't used at every log site. The highest-risk gap is the **Google provider**: `requests.HTTPError.__str__` includes the full request URL, which contains `?key=<api_key>` as a query parameter. Any `logger.error(f"... {e}")` after `raise_for_status()` leaks the key through the exception message.

---

### Files to modify / delete

| File | Action | Why |
|---|---|---|
| `backend/core/ai_providers.py` | Modify | Sanitize `{e}` in Google/Grok error logs; use `mask_secret()` or drop key-containing exception strings |
| `backend/core/ai_analytics.py` | None | Line 477 is `logger.info("Generating AI-powered analysis summary")` — safe, no credential |
| `dashboard.py` | Modify | Migrate 6 root-level imports to `backend.core` before deletion |
| `ai_providers.py` (root) | **Delete** | Sole consumer is `dashboard.py`; remove after import migration |
| `ai_analytics.py` (root) | **Delete** | Same; also carries its own root `from ai_providers import` |

---

### Specific fixes

- **Google `except Exception as e` (line 164):** Replace `logger.error(f"Google API error: {e}")` with `logger.error(f"Google API error: {type(e).__name__}")` — drops the URL (and embedded key) from the message entirely.
- **Grok debug log (line ~190 original):** Verify no key preview is logged; if any is present, use `mask_secret(self.api_key)` (last 4 chars only).
- **`AIProviderFactory` lines 237/246:** Currently logs `provider_name`, not `api_key` — safe, but switch from f-strings to `%s` style to eliminate CodeQL taint-flow false positives.

---

### No data model, API, or frontend changes.

---

### Testing strategy

1. Unit tests for `mask_secret` edge cases (empty, short, normal).
2. Log-capture tests per provider: mock `HTTPError` with a fake key in the URL; assert raw key absent from captured logs.
3. Import smoke test after deletion: `python -c "from dashboard import app"` must not raise `ImportError`.
4. `pytest backend/` green — masking is log-only, no behavioral changes.
5. CodeQL re-scan must show 0 `py/clear-text-logging-sensitive-data` alerts.

**Deletion blocker:** `dashboard.py`'s 6 root-level imports must be migrated first — do not delete root files until `grep` confirms no remaining non-`backend/core` references.
