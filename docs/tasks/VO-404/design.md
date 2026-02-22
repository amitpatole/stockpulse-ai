# VO-404: Incorrect error handling in news feed endpoint returns 500 instead of 400

## Technical Design

---

### 1. Approach

Introduce a `_parse_pagination()` helper in `backend/api/news.py` that validates the `page` and `page_size` query parameters before use. The helper calls `int()` inside a try/except to catch non-integer strings, then range-checks both values. On failure it returns a `(response, 400)` tuple; callers return it immediately. No try/except is needed in the view itself — the helper centralises all validation and returns a clear 400 before any database access.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/news.py` — add `_parse_pagination()` helper; call it from `get_news()`
- **CREATE**: `backend/tests/test_news_api.py` — unit and integration tests for pagination validation and the three news endpoints

No other files are touched.

---

### 3. Data Model

No schema changes. This is a pure request-validation fix.

---

### 4. API Spec

No new endpoints. Corrected behaviour on existing endpoint:

**`GET /api/news`**

| Query param value | Before fix | After fix |
|---|---|---|
| `page=1` (valid) | 200 | 200 (unchanged) |
| `page=0` | **500** | **400** |
| `page=-5` | **500** | **400** |
| `page=abc` | **500** | **400** |
| `page_size=0` | **500** | **400** |
| `page_size=101` | **500** | **400** |
| `page_size=abc` | **500** | **400** |

Error response shapes:
```json
{"error": "page and page_size must be integers"}
{"error": "page must be a positive integer"}
{"error": "page_size must be between 1 and 100"}
```

---

### 5. Frontend Component Spec

Not applicable — this is a backend-only fix with no UI surface.

---

### 6. Verification

1. **Non-integer page → 400**: `curl '/api/news?page=abc'` must return `{"error": "page and page_size must be integers"}` with status 400, not 500.
2. **Zero/negative page → 400**: `curl '/api/news?page=0'` must return `{"error": "page must be a positive integer"}` with status 400, not 500.
3. **Out-of-range page_size → 400**: `curl '/api/news?page_size=200'` must return `{"error": "page_size must be between 1 and 100"}` with status 400.
4. **Valid params unaffected → 200**: `curl '/api/news?page=1&page_size=25'` must return 200 with `data`, `page`, `page_size`, `total`, and `has_next` fields.
