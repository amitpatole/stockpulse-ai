# VO-328: Add batch export to research briefs

## Technical Design

### 1. Approach

Add a `POST /api/research/briefs/export` endpoint that accepts a list of brief IDs and target format, streams back a single downloadable file (ZIP, CSV, or PDF). On the frontend, augment the existing `research/page.tsx` left-panel list with per-row checkboxes and an "Export Selected" toolbar that fires the export request and triggers a browser download.

---

### 2. Files to Create/Modify

- **CREATE**: `backend/utils/export_briefs.py` (ZIP, CSV, PDF generation logic)
- **MODIFY**: `backend/api/research.py` (add `/briefs/export` route)
- **MODIFY**: `frontend/src/lib/types.ts` (add `ExportFormat` union type)
- **MODIFY**: `frontend/src/lib/api.ts` (add `exportBriefs()` function)
- **MODIFY**: `frontend/src/app/research/page.tsx` (add checkboxes, export toolbar, progress indicator)

---

### 3. Data Model

No schema changes. Reads existing `research_briefs` columns: `id`, `ticker`, `title`, `content`, `agent_name`, `model_used`, `created_at`.

---

### 4. API Spec

**POST** `/api/research/briefs/export`

Request JSON:
```json
{ "ids": [1, 4, 7], "format": "zip" }
```
`format` ∈ `"zip" | "csv" | "pdf"`

Response (success): Binary file stream
```
Content-Type: application/zip          (or text/csv, application/pdf)
Content-Disposition: attachment; filename="research-brief-export-2026-02-22.zip"
```

Response (error):
```json
{ "error": "No IDs provided" }   // 400
{ "error": "Brief 99 not found" } // 404
```

**ZIP**: one `.md` file per brief, named `{ticker}-{id}.md`
**CSV**: columns — `id, ticker, title, agent_name, model_used, created_at, content`
**PDF**: one page break per brief using `reportlab`; title + metadata header + content body

---

### 5. Frontend Component Spec

**Inline changes to** `frontend/src/app/research/page.tsx`

**Selection state** (new `useState`):
```typescript
const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
const [exportFormat, setExportFormat] = useState<ExportFormat>('zip')
const [exporting, setExporting] = useState(false)
```

**Brief list row** — prepend a `<input type="checkbox">` to each row; toggling adds/removes `id` from `selectedIds`.

**Export toolbar** — rendered above the list when `selectedIds.size > 0`:
```
[ ZIP ▼ ]  [ Export Selected (3) ]
```
- Format `<select>`: ZIP / CSV / PDF
- Button disabled when `exporting === true`; shows spinner for batches >10 (checked against `selectedIds.size`)
- On click: calls `exportBriefs(ids, format)` → receives a `Blob` → triggers `<a download>` click

**`exportBriefs()` in `api.ts`:**
```typescript
export async function exportBriefs(ids: number[], format: ExportFormat): Promise<Blob>
// POST /api/research/briefs/export, returns response.blob()
```

**New type in `types.ts`:**
```typescript
export type ExportFormat = 'zip' | 'csv' | 'pdf'
```

**Empty state**: Export button absent when no briefs selected; no tooltip needed (button simply doesn't render).

---

### 6. Verification

1. **ZIP export**: Select 3 briefs, export as ZIP — downloaded file unzips to exactly 3 `.md` files with correct content and filename convention `research-brief-export-YYYY-MM-DD.zip`.
2. **CSV export**: Export 5 briefs as CSV — open in a spreadsheet and confirm all 7 columns present with no truncated content.
3. **Progress indicator**: Select 11 briefs and click Export — confirm spinner/loading state appears during the request and clears on completion.
