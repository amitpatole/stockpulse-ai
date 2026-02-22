# VO-400: Pagination off-by-one in settings persistence list endpoint

## Technical Design

Now I have everything I need. Here is the technical design spec:

---

### VO-362: Pagination Off-by-One in Settings Persistence List Endpoint

---

### 1. Approach

The `GET /api/settings/ai-providers` endpoint has three defects: it omits `total_pages` and `has_prev` from the response envelope, and it silently returns HTTP 200 with an empty list when the requested page exceeds the last valid page instead of a 400. All three fixes are isolated to `_parse_pagination` and the response block in `get_ai_providers_endpoint`. No schema changes or frontend components are required.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/settings.py` — fix `get_ai_providers_endpoint` response envelope (add `total_pages`, `has_prev`; add out-of-bounds page guard)
- **MODIFY**: `backend/tests/test_settings_api.py` — add regression tests for `total_pages`, `has_prev`, out-of-bounds page, and boundary counts (single item, exact-multiple, non-multiple)

---

### 3. Data Model

No changes. This is a pure logic fix; no new tables, columns, or migrations.

---

### 4. API Spec

**Existing endpoint** `GET /api/settings/ai-providers` — response envelope updated:

```json
{
  "data": [...],
  "page": 2,
  "page_size": 2,
  "total": 4,
  "total_pages": 2,
  "has_next": false,
  "has_prev": true
}
```

**Field definitions:**
| Field | Formula |
|---|---|
| `total_pages` | `ceil(total / page_size)` — use integer math `(total + page_size - 1) // page_size`; yields `1` when `total == 0` |
| `has_prev` | `page > 1` |
| `has_next` | `(page * page_size) < total` *(already correct, no change)* |

**Out-of-bounds guard** (insert before slicing, when `total > 0`):
```python
if page > total_pages:
    return jsonify({'error': f'page {page} exceeds total_pages {total_pages}'}), 400
```

When `total == 0`, page 1 is valid; page 2+ returns 400.

---

### 5. Frontend Component Spec

No new frontend component. The existing settings UI already pages via `has_next`; adding `total_pages` and `has_prev` to the response unlocks accurate "Page X of Y" display and a back-navigation control if a frontend ticket is filed later. No frontend changes are in scope for this fix.

---

### 6. Verification

1. **Exact-multiple boundary** — seed 4 providers, request `page=2&page_size=2`: expect `data` length 2, `has_next=false`, `has_prev=true`, `total_pages=2`. Then request `page=3&page_size=2`: expect HTTP 400.

2. **Non-multiple last page** — request `page=2&page_size=3` against 4 providers: expect `data` length 1 (the fourth item only), `has_next=false`, `total_pages=2`. Confirms no duplication and no empty page.

3. **Single-item corpus** — request `page=1&page_size=1`: expect `has_prev=false`, `has_next=false`, `total_pages=1`. Then request `page=2&page_size=1`: expect HTTP 400, confirming the out-of-bounds guard fires on the first page past the end.
