# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

## Technical Design Spec — VO-059: Fix Clear-Text Logging of Sensitive API Keys

---

### 1. Approach

Single-responsibility utility function + targeted call-site fixes. Create one `mask_secret()` helper, import it at each flagged site, and replace the offending log expressions. Root-level files cannot be deleted — they are actively imported by `dashboard.py` and `backend/core/ai_analytics.py` — so they receive identical fixes.

**`mask_secret(value: str) -> str`**
```python
def mask_secret(value: str | None) -> str:
    if not value or len(value) < 4:
        return "****"
    return f"****{value[-4:]}"
```

---

### 2. Files to Modify / Create

| Action | Path | Reason |
|--------|------|--------|
| **Create** | `backend/core/utils.py` | New home for `mask_secret()` |
| **Modify** | `backend/core/ai_providers.py` | Fix lines 147, 190, 246 |
| **Modify** | `backend/core/ai_analytics.py` | Fix line 477 |
| **Modify** | `ai_providers.py` *(root)* | Active — imported by `dashboard.py` and `backend/core/ai_analytics.py`; same fixes apply |
| **Modify** | `ai_analytics.py` *(root)* | Active — imported by `dashboard.py`; audit and fix any equivalent violations |

**Specific call-site changes:**

- **`ai_providers.py:190`** — Replace `api_key[:10]` with `mask_secret(api_key)`
- **`ai_providers.py:147`** — Replace `{error_msg}` (raw HTTP response body) with `status_code` only: `logger.error(f"Google API error: HTTP {response.status_code}")`
- **`ai_providers.py:246`** — Wrap exception: `logger.error(f"Error creating provider {provider_name}: {type(e).__name__}")` — drop `{e}` which may echo credential details from upstream
- **`ai_analytics.py:477`** — The log line accesses `provider_config['provider_name']` and `provider_config['model']` only, but CodeQL taints the whole dict. Fix: extract fields into locals before the log call so the taint flow is broken; no content change needed if fields don't include `api_key`

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

### 6. Testing Strategy

**Unit tests** (`backend/tests/test_utils.py`):
- `mask_secret("sk-abcdef1234")` → `"****1234"`
- `mask_secret("ab")` → `"****"` (short value)
- `mask_secret(None)` → `"****"` (None-safe)
- `mask_secret("")` → `"****"` (empty)

**Integration smoke test**: instantiate each provider with a dummy key, trigger the debug/error log paths, assert log output matches `r"\*{4}[A-Za-z0-9]{4}"` and does not contain the full key string.

**Regression**: run existing test suite; no behavioral code is touched, so all existing tests must stay green.

**CodeQL verification**: after merge, confirm the 8 alerts close on the next scheduled scan (or trigger manually via `gh workflow run codeql`).

---

**No schema, API, or UI impact. Rollout risk: minimal.**
