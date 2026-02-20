# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

Now I have a thorough picture of the codebase. Let me write the technical design spec.

---

## Technical Design Spec: VO-035 — Fix Clear-Text Logging of Sensitive Data

### Approach

Three surgical changes, in dependency order:

1. **Add a `mask_secret` helper** to `backend/core/ai_providers.py` and replace all sensitive-adjacent logger calls with masked output.
2. **Fix the root-cause import chain** — `dashboard.py` and `backend/core/ai_analytics.py` both import from root-level modules; migrate these to `backend.core` before deletion.
3. **Delete root-level duplicates** once confirmed unreferenced.

---

### Files to Modify / Create

| File | Action | Reason |
|---|---|---|
| `backend/core/ai_providers.py` | Modify | Add `mask_secret()` helper; fix Google URL key-in-querystring; sanitize all logger calls |
| `backend/core/ai_analytics.py:472` | Modify | Fix `from ai_providers import ...` → `from backend.core.ai_providers import ...` |
| `dashboard.py:240,249,259,361,387,388` | Modify | Migrate 6 imports from root-level to `backend.core` before deletion |
| `ai_providers.py` (root) | Delete | Confirmed duplicate; `dashboard.py` is the only consumer — fix that import first |
| `ai_analytics.py` (root) | Delete | Same; also references root-level `ai_providers` (circular) |

---

### `mask_secret` Helper (new, in `backend/core/ai_providers.py`)

```python
def mask_secret(value: str, show: int = 4) -> str:
    """Return a masked credential string, showing only the last `show` chars."""
    if not value or len(value) <= show:
        return "****"
    return f"****{value[-show:]}"
```

Place at module level, before the class definitions. Use it at every logger call site where `self.api_key` or a `provider_config` dict is in scope.

---

### Specific Logger Call Fixes

**`backend/core/ai_providers.py`** — active vulnerabilities:

- **Line 138 (Google URL construction):** `f"{self.base_url}?key={self.api_key}"` — the API key is embedded in the URL. Requests will include this URL in exception messages and potentially in debug logs. Fix: build URL separately and never log it; or switch to a `params=` dict and only log the masked key on failure, not the URL.
- **Lines ~147, ~195 area:** Any `logger.error` that references `error_msg` containing `response.text` could expose key material in provider error bodies. Scope-check what `response.text` may echo back (Google echoes the request URL including the key on 400s).
- **Lines 237/246 area (`create_provider` / `get_available_providers`):** Verify no `api_key` value flows into a format string passed to `logger`.

**`backend/core/ai_analytics.py:477`:** The `provider_config` dict (which contains `api_key`) must not flow into any logger call — current line 479 logs `safe_provider`/`safe_model` which is fine, but the surrounding code must not accidentally log the full dict.

---

### Data Model Changes

None.

### API Changes

None.

### Frontend Changes

None.

---

### Testing Strategy

1. **Unit test `mask_secret`** — assert correct masking for short strings, empty strings, normal-length keys.
2. **Log-capture tests** — for each provider's `generate_analysis`, mock `requests.post` to raise an exception containing a fake API key, then assert the captured log output does NOT contain the raw key value.
3. **Import smoke test** — after root-level file deletion, run `python -c "from dashboard import app"` and confirm no `ImportError`.
4. **Existing test suite** — `pytest backend/` must pass green; no functional behavior changes.
5. **Re-scan gate** — GitHub Code Scanning re-run must show 0 instances of `py/clear-text-logging-sensitive-data`.

---

**Critical prerequisite:** `dashboard.py`'s six root-level imports are the blocker for deletion. Fix those imports first — do not delete the root files until `grep -r "from ai_providers\|from ai_analytics" .` returns only `backend/core` paths.
