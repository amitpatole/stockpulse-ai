# VO-021: Memory leak in stock watchlist after prolonged usage

## Technical Design

Here's the design spec for VO-018:

---

## VO-018 Technical Design: Pagination off-by-one in settings AI providers endpoint

### Approach

`GET /api/settings/ai-providers` returns a bare JSON array today — no pagination at all. The off-by-one risk is introduced *when adding it*: `(page * page_size) < total` is correct; `<=` fires a phantom next-page when `total` is exactly divisible by `page_size`. Fix reuses the pattern already established in `news.py:_parse_pagination` and `news.py:91`. Pagination is applied by slicing the in-memory `result` list post-assembly — no SQL changes.

### Files to Modify

| File | What changes |
|---|---|
| `backend/api/settings.py` | Add `page`/`page_size` params to `get_ai_providers_endpoint`; slice assembled list; return standard `{data, page, page_size, total, has_next}` envelope |
| `frontend/src/lib/api.ts` | `getAIProviders()` (line 186): unwrap `response.data` instead of `response.providers` |
| `backend/tests/test_settings_api.py` | Update 5 existing tests to read `data['data']`; add 7 new pagination boundary tests |

### Data Model Changes

None. The list is assembled from `SUPPORTED_PROVIDERS` merged with DB rows — no schema changes.

### API Changes

`GET /api/settings/ai-providers` gains optional `page` (default 1) and `page_size` (default 25, range 1–100) params. Response shape changes from bare array to the same envelope used by `/api/news` and `/api/research/briefs`. The error fallback path must also return the envelope (not `[]`) so the frontend never sees an unexpected shape.

### Frontend Changes

Only `getAIProviders()` in `api.ts` changes — unwrap `.data` instead of `.providers`. Return type stays `AIProvider[]`; no component or route changes needed.

### Testing Strategy

Existing tests break on the shape change (they assert `isinstance(data, list)`) — update them to iterate `data['data']`. New boundary tests cover: exact-boundary `has_next: false` when `total == page_size` (the core bug), one-over boundary, page 2 offset correctness, and invalid `page_size` values (`0`, `101`, `-1` → 400). All tests use `unittest.mock.patch` on `get_all_ai_providers` — no DB seeding needed.
