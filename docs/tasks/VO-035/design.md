# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

Now I have enough context to write the spec. Here it is:

---

## Technical Design Spec: VO-035 — Prevent Clear-Text Logging of Sensitive Data

### Approach

Surgical fix in two backend files plus deletion of two stale root-level duplicates. No architectural change needed.

1. Add a private `_mask_key(key: str) -> str` helper at module level in `backend/core/ai_providers.py` that returns `f"...{key[-4:]}"` (safe fallback: `"...????"` for short/empty keys).
2. Replace every flagged `logger.*` call that touches `api_key`, `api_key_preview`, or `response.text` with safe alternatives — either using the masked key or truncating response bodies.
3. In `backend/core/ai_analytics.py`, ensure the `logger.info` near line 477 only references `provider_config['provider_name']` and `provider_config['model']` — never `provider_config['api_key']` or the full dict.
4. Confirm root-level `ai_providers.py` and `ai_analytics.py` are unreferenced, then delete them.

**Specific fixes in `backend/core/ai_providers.py`:**

| Approx. line | Current (unsafe) | Safe replacement |
|---|---|---|
| 147 | `f"...API Key: {api_key_preview}..."` (first 10 chars) | `f"...API Key: {_mask_key(self.api_key)}..."` |
| 190 | `error_msg = f"HTTP {status}: {response.text}"` | `error_msg = f"HTTP {status}: {response.text[:200]}"` (truncate, no key substitution) |
| 237 | `logger.error(f"Grok API response detail: {error_detail}")` | Omit or log only the `error` field from the parsed JSON, not the full dict |
| 246 | Similar response body log | Same truncation pattern |

**Fix in `backend/core/ai_analytics.py` (line ~477):**

Confirm the `logger.info` only interpolates `provider_config['provider_name']` and `provider_config['model']`. If any surrounding line logs the full `provider_config` dict, replace with field-by-field extraction.

---

### Files to Modify / Create / Delete

| Action | Path |
|---|---|
| Modify | `backend/core/ai_providers.py` |
| Modify | `backend/core/ai_analytics.py` |
| Delete | `ai_providers.py` (root) |
| Delete | `ai_analytics.py` (root) |
| Modify | `backend/tests/test_settings_api.py` or a new `backend/tests/test_ai_providers_masking.py` |

---

### Data Model Changes

None.

---

### API Changes

None. The `test_provider_connection` endpoint behavior is unchanged — masking is log-only.

---

### Frontend Changes

None.

---

### Testing Strategy

1. **Unit test for `_mask_key`** (new file `backend/tests/test_ai_providers_masking.py`):
   - Normal key → last 4 chars with `...` prefix
   - Key shorter than 4 chars → safe fallback `...????`
   - Empty string → safe fallback

2. **Verify no regression on existing suite** — run `backend/tests/` after changes; all tests must pass unchanged.

3. **Grep verification (pre-delete)** — confirm zero matches for `from ai_providers import` and `from ai_analytics import` (root-relative) across the entire repo before deleting the root files.

4. **CodeQL note** — the fixes target the exact data-flow patterns CodeQL traces: `api_key → logger.*` and `response.text → logger.*`. Masking breaks the taint flow; truncation without key interpolation removes the response-body vector.
