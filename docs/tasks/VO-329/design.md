# VO-329: Create batch export in research briefs

## Technical Design

### 1. Approach

Add a `POST /api/research/briefs/export` endpoint to the existing research blueprint that fetches selected brief IDs, delegates to the already-implemented `export_briefs.py` utilities, and streams a ZIP/CSV/PDF binary response. On the frontend, layer checkbox selection state onto the existing brief list in `research/page.tsx` and trigger a blob download via a new `exportBriefs()` API client function.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/research.py` — add `POST /briefs/export` route using existing `export_briefs.py`
- **MODIFY**: `frontend/src/lib/types.ts` — add `ExportFormat` union type
- **MODIFY**: `frontend/src/lib/api.ts` — add `exportBriefs(ids, format)` function returning `Blob`
- **MODIFY**: `frontend/src/app/research/page.tsx` — add checkbox column, selection toolbar, export button, progress indicator

---

### 3. Data Model

No new tables or columns required. All needed fields (`id`, `ticker`, `title`, `content`, `agent_name`, `model_used`, `tokens_used`, `estimated_cost`, `created_at`) already exist in `research_briefs`.

---

### 4. API Spec

**POST** `/api/research/briefs/export`

Request:
```json
{ "ids": [1, 4, 7], "format": "zip" }
```
- `ids`: array of integers, 1–100 items (400 if empty or >100)
- `format`: `"zip"` | `"csv"` | `"pdf"` (400 if unrecognized)

Response (success): Binary file stream
```
Content-Type: application/zip  (or text/csv, application/pdf)
Content-Disposition: attachment; filename="research-brief-export-2026-02-22.zip"
```

Response (error):
```json
{ "error": "Too many briefs selected (max 100)" }
```
- 400 for validation errors, 404 if any requested ID does not exist, 500 for generation failure. Partial failures within PDF/ZIP continue and append an error summary page/entry.

---

### 5. Frontend Component Spec

**Component**: `BatchExportToolbar` — inline in `frontend/src/app/research/page.tsx` (no separate file; small enough to colocate)

**Selection state**: `const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())`

**Brief list changes**:
- Prepend a `<input type="checkbox">` column to each row
- "Select All" / "Deselect All" toggle in list header (visible always)
- Row click continues to open detail view; checkbox click toggles selection only

**Toolbar** (appears above brief list when `selectedIds.size > 0`):
| Element | Detail |
|---|---|
| Count label | `{n} selected` |
| Format dropdown | `<select>`: ZIP, CSV, PDF |
| Export button | Disabled if `selectedIds.size === 0` or `> 100` |
| Progress spinner | Shown while `exporting === true` |
| Error banner | Inline text for partial/full failures |

**Renders in**: existing `<div>` left-panel of `frontend/src/app/research/page.tsx`

**Download trigger**:
```typescript
const blob = await exportBriefs([...selectedIds], format);
const url = URL.createObjectURL(blob);
const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
URL.revokeObjectURL(url);
```

**Loading state**: `exporting` boolean disables button and shows spinner.
**Error state**: catch block sets `exportError` string; displayed as red inline text below toolbar.

---

### 6. Verification

1. Select 3 briefs, export as ZIP — download a `.zip` containing 3 `.md` files named `{ticker}-{id}.md`, each with correct content and metadata headers.
2. Select 101 briefs — Export button shows disabled state with tooltip "Max 100 briefs per export"; backend also returns 400 if called directly.
3. Select briefs including one with a deleted/nonexistent ID (via direct API call with a bogus ID) — server returns 404; frontend shows error banner without crashing.
