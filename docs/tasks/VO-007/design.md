# VO-007: Technical Design — Fix Clear-Text Logging of Sensitive Data

## Approach

Add one `_mask_key(key: str) -> str` module-level helper in `backend/core/ai_providers.py` and apply it at all 5 flagged sites in the `backend/core/` files. The root-level `ai_providers.py` and `ai_analytics.py` **cannot be deleted** — `dashboard.py` imports directly from both — so they are converted to thin re-exports that delegate entirely to `backend/core/`. Once they contain no logging logic, the remaining 3 CodeQL findings on root-level files are eliminated automatically.

Masking format: `****<last4>` (e.g., a 32-char key ending in `ab12` → `****ab12`).

---

## Files to Modify

| File | Action |
|---|---|
| `backend/core/ai_providers.py` | Add `_mask_key()` helper; fix lines 147, 190, 246 |
| `backend/core/ai_analytics.py` | Fix line 477: log only safe fields from `provider_config` |
| `ai_providers.py` (root) | Replace full implementation with one-line re-export shim |
| `ai_analytics.py` (root) | Replace full implementation with one-line re-export shim |

### `backend/core/ai_providers.py` — helper + 3 fixes

```python
# At module level, before any class
def _mask_key(key: str) -> str:
    return "****" + key[-4:] if len(key) >= 4 else "****"
```

- **Line 147** (`GoogleProvider`): `response.text` may echo the key embedded in the request URL. Truncate and scrub before logging:
  ```python
  safe_body = response.text[:200].replace(self.api_key, _mask_key(self.api_key))
  logger.error(f"Google API error: HTTP {response.status_code}: {safe_body}")
  ```
- **Line 190** (`GrokProvider`): Current preview exposes first 10 chars. Replace with `_mask_key()`:
  ```python
  logger.debug(f"Grok API request - Model: {self.model}, Key: {_mask_key(self.api_key)}, URL: {self.base_url}")
  ```
- **Line 246** (`AIProviderFactory.create_provider`): Exception `str(e)` can contain the key. Sanitize inline:
  ```python
  logger.error(f"Error creating provider {provider_name}: {str(e).replace(api_key, _mask_key(api_key))}")
  ```
- **Line 237**: Logs only `provider_name` — no key reference; no change needed.

### `backend/core/ai_analytics.py` — line 477

The log line itself is safe, but CodeQL's taint trace follows `provider_config` (which holds `api_key`) into the surrounding block. Fix: extract only safe fields before any log call so the tainted dict never appears in logging context:

```python
provider_name = provider_config['provider_name']
model = provider_config['model']
logger.info(f"Using AI provider: {provider_name} - {model}")
```

### Root-level shims

Both files become two-line shims so `dashboard.py` imports continue to resolve unchanged:

```python
# ai_providers.py  (replaces entire file)
from backend.core.ai_providers import *  # noqa: F401, F403
```
```python
# ai_analytics.py  (replaces entire file)
from backend.core.ai_analytics import *  # noqa: F401, F403
```

> **Out of scope**: `backend/core/ai_analytics.py` line 472 contains a bare `from ai_providers import AIProviderFactory`. This pre-existing import style issue is tracked under VO-002 and must not be changed here.

---

## Data Model Changes

None.

---

## API Changes

None.

---

## Frontend Changes

None.

---

## Testing Strategy

1. **Import smoke tests** — run after converting root files to shims:
   ```bash
   python -c "from backend.core.ai_providers import AIProviderFactory; print('ok')"
   python -c "from ai_providers import AIProviderFactory; print('ok')"
   python -c "from ai_analytics import StockAnalytics; print('ok')"
   ```

2. **Unit tests for `_mask_key`** — add to the existing provider test file:
   - `len(key) < 4` → `"****"`
   - `len(key) == 4` → `"****" + key`
   - Normal 32-char key → `"****" + key[-4:]`

3. **Regression** — existing suite must pass with no changes:
   ```bash
   pytest backend/tests/ tests/ -q
   ```

4. **CodeQL gate** — push branch; GitHub Code Scanning must report 0 instances of `py/clear-text-logging-sensitive-data`.
