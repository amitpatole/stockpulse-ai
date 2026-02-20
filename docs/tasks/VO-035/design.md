# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

Now I have the full picture. Let me write the spec.

---

## Technical Design Spec: VO-035 — Mask Sensitive Data in Application Logs

### 1. Approach

Two distinct fix vectors, applied consistently to both the `backend/core/` versions and the root-level duplicates (which `dashboard.py` actively imports):

**Vector A — Google Provider URL leak.** `self.api_key` is embedded in the request URL at `backend/core/ai_providers.py:145`. When `requests` raises an exception (e.g. `ConnectionError`, `HTTPError`), the exception message includes the full URL with the raw key. Fix: move the key from the query string to the `x-goog-api-key` request header. This eliminates the taint path entirely — no URL reconstruction needed in the exception handler.

**Vector B — Factory constructor taint path.** CodeQL flags lines 237/246 in `AIProviderFactory.create_provider()` because `api_key` flows into `provider_class(api_key, ...)` and the bare `except` at line 249 logs `{e}`, which could surface the key if the constructor's exception message references it. Fix: the exception log at line 249 already logs `type(e).__name__: {e}` — change it to log only `type(e).__name__` and `provider_name`, dropping `{e}` which is the taint carrier.

**Root-level files:** `dashboard.py` imports `ai_providers` and `ai_analytics` directly from the project root (lines 240, 249, 259, 361, 387, 388). These are independent copies, not re-exports. Apply the identical fixes to both root-level copies. Do **not** delete them — that would break `dashboard.py`.

---

### 2. Files to Modify

| File | Change |
|---|---|
| `backend/core/ai_providers.py` | Move Google API key to header (lines 128–149); tighten factory exception log (line 249) |
| `ai_providers.py` (root) | Same two changes — mirror exactly |
| `backend/core/ai_analytics.py` | Verify line 477 region; confirm `provider_config` dict is never logged whole |
| `ai_analytics.py` (root) | Same verification/fix — mirror exactly |

No new files created. No files deleted.

---

### 3. Data Model Changes

None.

---

### 4. API Changes

None. The Google API still accepts `x-goog-api-key` as a header — this is the documented alternative to the `?key=` query param and requires no server-side change.

---

### 5. Frontend Changes

None.

---

### 6. Testing Strategy

**Unit tests (existing suite):**
- Verify `GoogleProvider.generate_analysis()` request is made with `x-goog-api-key` header and no `?key=` in the URL (mock `requests.post`, assert `call_args`).
- Verify factory exception path does not include raw `api_key` string in logged output (capture log records, assert key not present).

**Grep verification (CI-gatable):**
```bash
# Must return zero matches after fix
grep -n "logger.*api_key\|logger.*self\.api_key" \
  backend/core/ai_providers.py ai_providers.py \
  backend/core/ai_analytics.py ai_analytics.py
```

**CodeQL:** Re-run GitHub Code Scanning on the branch; expect zero `py/clear-text-logging-sensitive-data` findings in the four affected files.

**Smoke test:** Run `dashboard.py` against a dev environment; confirm AI provider selection and `test_provider_connection` still function correctly.
