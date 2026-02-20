# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design Spec — VO-035: Mask Sensitive Data in Application Logs

### Approach

Surgical, three-part fix with no architectural changes. No new tables, endpoints, or frontend components are required.

**Part 1 — Add `mask_secret()` helper and patch `backend/core/ai_providers.py`.**

`backend/core/utils.py` does not exist; `mask_secret()` is not yet defined anywhere in the codebase. Add a module-level helper directly in `backend/core/ai_providers.py` (above the class definitions):

```python
def mask_secret(secret: str) -> str:
    """Return a masked version of a secret, showing only the last 4 characters."""
    if not secret or len(secret) <= 4:
        return "****"
    return "****" + secret[-4:]
```

Then apply it to each flagged line:

- **Line 147** (`GoogleProvider.generate_analysis`): `response.text` in `error_msg` can reflect request content including the URL-embedded API key. Change to log only the status code:
  ```python
  logger.error(f"Google API error: HTTP {response.status_code}")
  ```
- **Line 190** (`GrokProvider.generate_analysis`): Replace the hand-rolled `[:10] + "..."` preview with `mask_secret(self.api_key)` for consistency.
- **Line 237** (`AIProviderFactory.create_provider`): This line logs only `provider_name` (no secret in scope). Verify scanner alert is a false positive from proximity; no change needed if confirmed. If flagged due to `api_key` parameter on the same call frame, guard by logging only the provider class name.
- **Line 246** (`AIProviderFactory.create_provider` except block): `{e}` in exception strings from HTTP libraries can embed the original request URL, which contains the API key for Google's URL-key pattern. Change to:
  ```python
  logger.error(f"Error creating provider {provider_name}: {type(e).__name__}")
  ```

**Part 2 — Patch `backend/core/ai_analytics.py` line 477.**

Line 477 as written only logs `provider_name` and `model` — already safe. However, to prevent future regressions where someone adds `api_key` to `provider_config` and the log silently expands, make the safe fields explicit with local variable extraction:

```python
provider_name = provider_config['provider_name']
model = provider_config['model']
logger.info(f"Using AI provider: {provider_name} - {model}")
```

**Part 3 — Redirect root-level imports then delete duplicate files.**

`ai_providers.py` and `ai_analytics.py` at the repo root are flagged by the scanner. Contrary to an earlier draft of this spec, they are **actively imported** by:

- `dashboard.py` (lines 240, 249, 259, 361, 387, 388) — bare `from ai_providers import ...` and `from ai_analytics import StockAnalytics`
- `backend/core/ai_analytics.py` (line 472) — `from ai_providers import AIProviderFactory`

**Deletion requires fixing imports first.** Update these callers to use `backend.core.*` canonical paths before deleting the root files. After redirecting all callers, delete both root files. Note: existing `test_vo002_*` test suites already assert these bare imports must not exist, so fixing the imports also unblocks those test assertions.

---

### Files to Modify / Delete

| Action | Path | Notes |
|--------|------|-------|
| Modify | `backend/core/ai_providers.py` | Add `mask_secret()` helper; patch lines 147, 190, 246 |
| Modify | `backend/core/ai_analytics.py` | Fix line 477 (explicit field extraction); fix line 472 import |
| Modify | `dashboard.py` | Redirect root-level imports to `backend.core.*` |
| Delete | `ai_providers.py` (root) | After all callers redirected |
| Delete | `ai_analytics.py` (root) | After all callers redirected |

---

### Data Model Changes

None.

---

### API Changes

None.

---

### Frontend Changes

None.

---

### Testing Strategy

1. **Grep assertion** — `grep -rn "self\.api_key" backend/ | grep "logger\."` must return empty after the patch.
2. **Grep assertion** — `grep -rn "from ai_providers import\|from ai_analytics import" dashboard.py backend/` must return empty after import redirect (bare root imports gone).
3. **Existing test suite** — `pytest backend/ tests/` must pass with zero new failures. The `test_vo002_*` suites assert bare root imports are absent; they should now pass.
4. **Import smoke test** — `python -c "from backend.core.ai_providers import AIProviderFactory; from backend.core.ai_analytics import StockAnalytics"` must succeed after root-file deletion.
5. **Manual log review** — Trigger one provider call in dev; confirm logs show `****xxxx` format for any key reference, never a raw key.
6. **Code scanning** — Merge to main; confirm GitHub Advanced Security shows 0 `py/clear-text-logging-sensitive-data` alerts.
