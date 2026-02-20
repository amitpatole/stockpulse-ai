# VO-018: Pagination off-by-one in settings page list endpoint

## Technical Design

---

### Approach

`GET /api/settings/ai-providers` currently returns a bare JSON array. The off-by-one risk
lives in the `has_next` predicate: using `<=` instead of `<` would fire a phantom next-page
whenever `total` is exactly divisible by `page_size`. The fix is to add pagination to the
endpoint using the same helper and formula already proven in `news.py` and `research.py`,
then update the frontend client to unwrap the new envelope shape.

No DB queries involved — the provider list is assembled in memory by merging
`SUPPORTED_PROVIDERS` with DB rows, so pagination is a post-assembly slice.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/api/settings.py` | Add `page`/`page_size` query params to `get_ai_providers_endpoint`; apply `_parse_pagination` helper (import from `news.py` or inline); slice `result[offset:offset+page_size]`; return `{data, page, page_size, total, has_next}` envelope |
| `frontend/src/lib/api.ts` | Update `getAIProviders()` (line 186): unwrap `response.data` instead of `response.providers`; return type stays `AIProvider[]` |
| `backend/tests/test_settings_api.py` | Update existing tests that assert `isinstance(data, list)` to assert on `data['data']`; add new pagination boundary tests |

---

### Data Model Changes

None. The provider list is static (`SUPPORTED_PROVIDERS` dict merged with DB rows). No
schema changes.

---

### API Changes

`GET /api/settings/ai-providers`

New query params (same validation as `news.py:_parse_pagination`):
- `page` — integer ≥ 1, default `1`
- `page_size` — integer 1–100, default `25`; returns `400` with `{"error": "..."}` on invalid value

Response shape changes from bare array to standard envelope:
```json
{
  "data": [ ...provider objects... ],
  "page": 1,
  "page_size": 25,
  "total": 4,
  "has_next": false
}
```

`has_next` formula: `(page * page_size) < total` — matching `news.py:91` exactly.

Error fallback path (`except Exception`) must also return the envelope shape:
`{"data": [], "page": 1, "page_size": page_size, "total": 0, "has_next": false}`.

---

### Frontend Changes

**`frontend/src/lib/api.ts` — `getAIProviders()` (line 186)**

Change unwrapping from `data.providers` to `data.data`:
```ts
// before
const data = await request<{ providers: AIProvider[] } | AIProvider[]>(...);
if (Array.isArray(data)) return data;
return Array.isArray(data.providers) ? data.providers : [];

// after
const data = await request<{ data: AIProvider[]; has_next: boolean } | AIProvider[]>(...);
if (Array.isArray(data)) return data;   // keep legacy fallback for safety
return Array.isArray(data.data) ? data.data : [];
```

No component or route changes needed — callers of `getAIProviders()` receive the same
`AIProvider[]` type.

---

### Testing Strategy

**Update existing tests in `backend/tests/test_settings_api.py`:**
- `test_zero_data_user_returns_list` → assert on `data['data']` being a list, not `data` itself
- `test_zero_data_user_all_providers_unconfigured` → iterate `data['data']`
- `test_zero_data_user_required_keys_present` → iterate `data['data']`
- `test_zero_data_user_known_providers_included` → read names from `data['data']`
- `test_configured_provider_marked_correctly` → read providers from `data['data']`

**New boundary tests (add to `TestGetAIProviders` or a new `TestGetAIProvidersPagination` class):**

| Test | Scenario |
|---|---|
| `test_envelope_keys_present` | Response has `data`, `page`, `page_size`, `total`, `has_next` |
| `test_has_next_false_when_total_equals_page_size` | `total=4, page_size=4` → `has_next=False` (the off-by-one boundary) |
| `test_has_next_true_when_total_exceeds_page_size` | `total=4, page_size=3` → `has_next=True` |
| `test_page2_offset_correct` | `page=2, page_size=2` returns second slice of providers |
| `test_page_size_0_returns_400` | Invalid `page_size=0` → HTTP 400 |
| `test_page_size_101_returns_400` | Invalid `page_size=101` → HTTP 400 |
| `test_db_error_returns_envelope_not_bare_array` | Exception path returns `{data:[], ...}`, not `[]` |

All backend tests use the Flask test client with `unittest.mock.patch` on
`backend.api.settings.get_all_ai_providers` — no real DB or seed data needed.
