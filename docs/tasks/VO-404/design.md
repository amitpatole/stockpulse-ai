# VO-404: Incorrect error handling in news feed endpoint returns 500 instead of 400

## Technical Design

I have a clear picture of the bug. The `page` parameter in `_parse_pagination()` validates `page_size` (lines 30–31) but has no lower-bound guard on `page` itself — `page=0` or `page=-1` generates a negative `OFFSET` in the SQL query, causing SQLite to raise `OperationalError` which bubbles up as a 500. Here's the spec.

---

### 1. Approach

Add a `page >= 1` range check inside the existing `_parse_pagination()` helper in `backend/api/news.py`, immediately after the `page_size` range check, so that any non-positive `page` value returns `400` with a descriptive JSON error before the database is touched. This mirrors the already-correct `page_size` guard and keeps all input validation co-located in the helper. No other files need to change.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/news.py` — extend `_parse_pagination()` to reject `page < 1`
- **MODIFY**: `backend/tests/test_news_api.py` — add `TestGetNewsPageValidation` class covering the missing cases

---

### 3. Data Model

None. This is a pure validation fix; no schema changes.

---

### 4. API Spec

No new endpoints. Patch behaviour of the existing endpoint:

**`GET /api/news`** — updated validation table:

| Parameter | Valid range | On violation |
|-----------|-------------|-------------|
| `page` | integer ≥ 1 | `400 {"error": "page must be a positive integer"}` |
| `page_size` | integer 1–100 | `400 {"error": "page_size must be between 1 and 100"}` *(unchanged)* |

Error body shape is consistent with existing convention — single `"error"` key, plain string value:

```json
{ "error": "page must be a positive integer" }
```

`500` responses are reserved exclusively for DB/infrastructure failures, unchanged.

---

### 5. Frontend Component Spec

Not applicable. The frontend already passes `page` as a positive integer from its pagination controls; no frontend change is needed. The fix is purely defensive at the API layer.

---

### 6. Verification

1. **Reproduces the bug, then confirms the fix**: `curl "localhost:5000/api/news?page=0"` should return `HTTP 400` with `{"error": "page must be a positive integer"}` — not a 500 stack trace. Repeat with `page=-1`.
2. **Happy path regression**: `curl "localhost:5000/api/news?page=1&page_size=25"` returns `HTTP 200` with the full envelope (`data`, `page`, `page_size`, `total`, `has_next`).
3. **Boundary**: `curl "localhost:5000/api/news?page=1&page_size=0"` still returns `400` (existing `page_size` guard untouched); `page=999` with an empty DB returns `200` with an empty `data` array and `has_next: false`.
