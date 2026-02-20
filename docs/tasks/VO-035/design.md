# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

Good — I now have the full picture. Here's the design spec:

---

## VO-038 Technical Design Spec: Clear-Text Logging of Sensitive Data

### Approach

Introduce a single `mask_secret()` utility, apply it at all flagged logger call sites in the canonical `backend/core/` modules, fix a stale internal import in `ai_analytics.py`, redirect `dashboard.py` off the root-level duplicates, then delete the duplicates. No behavioral change — pure defensive logging hygiene.

**Important finding:** Neither root-level file is unused. `dashboard.py` imports from both (`ai_analytics.py` at lines 240/249/259/388 and `ai_providers.py` at lines 361/387). Additionally, `backend/core/ai_analytics.py` line 472 contains a runtime import `from ai_providers import AIProviderFactory` — pointing at the root-level copy, not the backend one. Both issues must be fixed before deletion is safe.

---

### Files to Modify / Create

| File | Action |
|---|---|
| `backend/core/utils.py` | **CREATE** — add `mask_secret()` helper |
| `backend/core/ai_providers.py` | **MODIFY** — fix lines 147, 190, 237, 246 |
| `backend/core/ai_analytics.py` | **MODIFY** — fix line 477 log + fix line 472 stale import |
| `dashboard.py` | **MODIFY** — redirect 5 imports from root → `backend.core.*` |
| `ai_providers.py` (root) | **DELETE** |
| `ai_analytics.py` (root) | **DELETE** |

---

### Change Details

**`backend/core/utils.py` (new)**
```python
def mask_secret(value: str) -> str:
    """Return masked version of a secret — last 4 chars only."""
    if value and len(value) >= 8:
        return f"****{value[-4:]}"
    return "****"
```

**`backend/core/ai_providers.py` — 4 sites**

- **Line 147** (Google HTTP error): `response.text` is untrusted; CodeQL taints it via the auth headers. Log only the status code: `logger.error(f"Google API error: HTTP {response.status_code}")`
- **Line 190** (Grok debug): Replace `[:10]` preview (still flagged by CodeQL) with `mask_secret(self.api_key)`
- **Line 237** (unknown provider): CodeQL taints all logs in functions that receive `api_key`. No sensitive data on the line itself, but restructure `create_provider` to not log inside a function receiving a raw key — move unknown-provider check to a guard before entering the try block, or suppress this log and raise instead.
- **Line 246** (provider creation failure): `str(e)` can echo the api_key passed to a constructor. Replace with: `logger.error(f"Error creating provider {provider_name}: {mask_secret(api_key)} — {type(e).__name__}")`

**`backend/core/ai_analytics.py` — 2 changes**

- **Line 472**: Change `from ai_providers import AIProviderFactory` → `from backend.core.ai_providers import AIProviderFactory` (or `from .ai_providers import AIProviderFactory` if package is configured for relative imports)
- **Line 477**: The log itself is clean, but CodeQL taints `provider_config` because `api_key` is accessed on lines 482–483 from the same variable. Fix: log explicitly keyed fields only — `logger.info(f"Using AI provider: {provider_config['provider_name']} / {provider_config['model']}")` — and confirm no `api_key` field appears anywhere in log context

**`dashboard.py` — redirect 5 imports**

Change root-relative imports to package imports:
```python
# Before
from ai_analytics import StockAnalytics
from ai_providers import AIProviderFactory, test_provider_connection

# After
from backend.core.ai_analytics import StockAnalytics
from backend.core.ai_providers import AIProviderFactory, test_provider_connection
```

Verify `dashboard.py` runs with `PYTHONPATH` set to project root (it should, given the existing `backend.core.*` imports in agents and API layers).

---

### Data Model Changes
None.

### API Changes
None.

### Frontend Changes
None.

### Testing Strategy

1. **Static verification**: `git grep -rn "api_key" backend/ | grep logger` → zero hits
2. **Smoke test `dashboard.py` imports**: `python -c "import dashboard"` from project root after deletion
3. **Existing test suite**: run `pytest` — no behavioral change, all tests should pass unchanged
4. **CodeQL**: alerts resolve automatically on next scan once the taint chains are broken at the logger call sites
