# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

## Technical Design Spec: VO-035 — Fix Clear-Text Logging of Sensitive Data

---

### 1. Approach

A `mask_secret()` helper **already exists** at `backend/core/utils.py:9`. The fix is purely mechanical: import and apply it at every flagged log call. No new abstractions needed.

The root-level files (`ai_providers.py`, `ai_analytics.py`) are **not deleted** — they are live runtime dependencies (`dashboard.py` → `ai_analytics.py` → `from ai_providers import AIProviderFactory`). They receive identical masking fixes in place.

The ad-hoc masking already present in `GrokProvider` (showing first 10 chars) is actually **less secure** than `mask_secret()` (shows last 4) and gets replaced.

---

### 2. Files to Modify / Create

| File | Action |
|---|---|
| `backend/core/ai_providers.py` | Fix lines 147, 190, 237, 246 — import `mask_secret` from `.utils`, replace raw key refs |
| `backend/core/ai_analytics.py` | Fix line 477 — mask `provider_config['api_key']` before logging |
| `ai_providers.py` (root) | Mirror identical changes; import `mask_secret` from `backend.core.utils` |
| `ai_analytics.py` (root) | Mirror identical changes |
| `backend/tests/test_mask_secret.py` | **Create** — unit tests for `mask_secret` + smoke tests on the log calls |

`backend/core/utils.py` — **no changes needed**, helper is already correct.

---

### 3. Data Model Changes

None.

---

### 4. API Changes

None.

---

### 5. Frontend Changes

None.

---

### 6. Specific Code Changes

**`backend/core/ai_providers.py`** — add at top of file:
```python
from .utils import mask_secret
```

Replace each flagged log site pattern:
```python
# Before (line 147 pattern — OpenAI/Anthropic key in debug/error log)
logger.debug(f"... api_key={self.api_key} ...")

# After
logger.debug(f"... api_key={mask_secret(self.api_key)} ...")
```

Line 190 specifically replaces the ad-hoc `api_key_preview` pattern entirely:
```python
# Before
api_key_preview = self.api_key[:10] + "..." if len(self.api_key) > 10 else "***"
logger.debug(f"Grok API request - Model: {self.model}, API Key: {api_key_preview}, ...")

# After
logger.debug(f"Grok API request - Model: {self.model}, API Key: {mask_secret(self.api_key)}, ...")
```

**Root-level `ai_providers.py`** — same changes; import path becomes:
```python
from backend.core.utils import mask_secret
```

**`backend/core/ai_analytics.py` line 477** — never log raw config dict fields:
```python
# Before
logger.info(f"Using AI provider: {provider_config['provider_name']} - {provider_config['model']}")
# (safe — no key here, but line 477 logs api_key directly; replace that)

# After — only log non-secret fields; mask the key reference
logger.debug(f"Provider api_key: {mask_secret(provider_config.get('api_key', ''))}")
```

---

### 7. Testing Strategy

**`backend/tests/test_mask_secret.py`** covers:
- `mask_secret(None)` → `"****"`
- `mask_secret("")` → `"****"`
- `mask_secret("short")` → `"****"` (< 8 chars)
- `mask_secret("sk-abcdef1234")` → `"****1234"`
- Assert raw key value does **not** appear in the returned string

**Smoke test**: instantiate each provider class with a dummy key, call the internal method that triggers the log line, capture `logging` output via `unittest.mock.patch`, assert the raw key is absent and `****` is present.

All existing tests must continue to pass — changes are additive imports + string substitutions only.
