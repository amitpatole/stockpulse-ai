# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

---

## Technical Design Spec: VO-035 — Redact Sensitive Data from Application Logs

### 1. Approach

Add a single `_mask_key(value)` helper inline to each affected module (no new shared module — the files are not yet on a clean import path from each other). Replace every flagged `logger.*` call that touches a credential or raw provider error body with a masked or sanitized version. The root-level `ai_providers.py` and `ai_analytics.py` **cannot be deleted** — the exploration confirms `dashboard.py` imports them directly and `backend/core/ai_analytics.py` also imports from the root-level `ai_providers.py`. They require the same masking fixes as their backend/core counterparts.

---

### 2. Files to Modify

| File | Action |
|---|---|
| `backend/core/ai_providers.py` | Add `_mask_key()`, fix lines 147, 190, 210, 244 |
| `backend/core/ai_analytics.py` | Add `_mask_key()`, fix line ~477/498 area |
| `ai_providers.py` (root) | Same masking fixes as backend/core version |
| `ai_analytics.py` (root) | Same masking fixes as backend/core version |
| `backend/tests/test_mask_key.py` | **New** — unit tests for `_mask_key()` |

No files deleted. A follow-up ticket should consolidate the duplicate module architecture.

---

### 3. The `_mask_key()` Helper

```python
def _mask_key(value: str | None) -> str:
    if not value:
        return "****"
    return f"****{value[-4:]}" if len(value) > 4 else "****"
```

Placed at module level in each affected file, just below the `logger = ...` line.

---

### 4. Specific Logger Call Fixes

**`ai_providers.py` (both copies) — flagged lines:**
- Line 147: Replace raw `response.status_code` / error body with truncated status only — no response content.
- Line 190: `logger.debug(f"Grok API request - Model: {self.model}, URL: {self.base_url}")` → strip URL or replace with `"[redacted]"`.
- Line 210: `logger.error(f"Grok API response detail: {error_detail}")` → truncate to first 100 chars and strip any key-like tokens, or drop entirely.
- Line 244: Exception message referencing `provider_name` is safe (it's a provider type name, not a credential), but the raw `str(e)` must not be logged — use `type(e).__name__` only.

**`ai_analytics.py` (both copies) — flagged line ~477/498:**
- Raw exception `f"Error generating AI summary: {e}"` — replace with `f"Error generating AI summary: {type(e).__name__}"`.

---

### 5. Data Model / API / Frontend Changes

None. This is purely a logging hygiene fix with no surface-area changes.

---

### 6. Testing Strategy

**New file `backend/tests/test_mask_key.py`:**
- `_mask_key(None)` → `"****"`
- `_mask_key("")` → `"****"`
- `_mask_key("ab")` → `"****"` (short string, no tail exposed)
- `_mask_key("sk-abcdefgh1234")` → `"****1234"`
- `_mask_key("x" * 40)` → `"****xxxx"` (normal API key length)

**Regression:** Run existing test suite (`pytest backend/`) — no behavior changes expected. Verify no test asserts on the old log message strings.
