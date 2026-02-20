# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

Good — there's already a `docs/tasks/VO-007/design.md` in the repo. I've verified its recommendations against the live code. The design is accurate. Here's the canonical spec:

---

## VO-035 Technical Design: Mask Sensitive Data in Log Output

### Approach

Add a single `_mask_key(key: str) -> str` helper in `backend/core/ai_providers.py` and apply it at all flagged log sites in the `backend/core/` files. The root-level `ai_providers.py` and `ai_analytics.py` are **not dead code** — `dashboard.py` imports from both at runtime — so they become thin re-export shims rather than being deleted. Once they contain no logging logic, the 3 CodeQL findings on root-level files resolve automatically.

Mask format: `****<last4>` (e.g. key ending in `ab12` → `****ab12`).

---

### Files to Modify

| File | Action |
|---|---|
| `backend/core/ai_providers.py` | Add `_mask_key()` at module level; fix lines 147, 190, 246 |
| `backend/core/ai_analytics.py` | Fix line 477: extract safe fields before logging, drop `provider_config` dict from log context |
| `ai_providers.py` (root) | Replace 303-line duplicate with one-line re-export shim |
| `ai_analytics.py` (root) | Replace 494-line duplicate with one-line re-export shim |

**Specific fixes:**

- **Line 147** (`GoogleProvider`): `response.text` may echo the key from the URL. Scrub before logging:
  ```python
  safe_body = response.text[:200].replace(self.api_key, _mask_key(self.api_key))
  logger.error(f"Google API error: HTTP {response.status_code}: {safe_body}")
  ```
- **Line 190** (`GrokProvider`): Current preview leaks first 10 chars — wrong direction. Replace:
  ```python
  logger.debug(f"Grok API request - Model: {self.model}, Key: {_mask_key(self.api_key)}, URL: {self.base_url}")
  ```
- **Line 237**: Logs only `provider_name` — no key reference. **No change needed.**
- **Line 246** (`AIProviderFactory`): Exception `str(e)` can carry the key. Sanitize inline:
  ```python
  logger.error(f"Error creating provider {provider_name}: {str(e).replace(api_key, _mask_key(api_key))}")
  ```
- **Line 477** (`ai_analytics.py`): CodeQL taint-traces `provider_config` (which holds `api_key`) into the surrounding log context. Extract only safe fields:
  ```python
  provider_name = provider_config['provider_name']
  model = provider_config['model']
  logger.info(f"Using AI provider: {provider_name} - {model}")
  ```

**Root-level shims** (so `dashboard.py` imports continue resolving unchanged):
```python
# ai_providers.py  — entire file
from backend.core.ai_providers import *  # noqa: F401, F403
```
```python
# ai_analytics.py  — entire file
from backend.core.ai_analytics import *  # noqa: F401, F403
```

> Out of scope: `backend/core/ai_analytics.py:472` contains a bare `from ai_providers import AIProviderFactory` — a pre-existing import style issue tracked under VO-002. Do not touch it here.

---

### Data Model / API / Frontend Changes

None.

---

### Testing Strategy

1. **Import smoke tests** after shim conversion:
   ```bash
   python -c "from backend.core.ai_providers import AIProviderFactory; print('ok')"
   python -c "from ai_providers import AIProviderFactory; print('ok')"
   python -c "from ai_analytics import StockAnalytics; print('ok')"
   ```
2. **Unit tests for `_mask_key`** in the existing provider test file — three cases: `len < 4` → `"****"`, `len == 4` → `"****" + key`, normal 32-char key → `"****" + key[-4:]`.
3. **Regression**: `pytest backend/tests/ tests/ -q` — no new failures.
4. **CodeQL gate**: push branch; scanning must report 0 instances of `py/clear-text-logging-sensitive-data`.
