# VO-355: Support batch export in research briefs

## Technical Design

Now I have a complete picture. Let me write the spec.

---

## Technical Design Spec: Batch Export Research Briefs

### 1. Approach

The frontend already contains ~80% of this feature: per-row checkboxes, select-all, a batch export toolbar, `handleExport`, and the `exportBriefs` API call are all live in `frontend/src/app/research/page.tsx`. The remaining gaps are: (a) a backend capabilities endpoint to expose PDF availability so the frontend can disable that option with a tooltip, (b) pagination on the briefs list with cross-page selection persistence, and (c) a reusable `Toast` component for 404/error feedback. No backend changes to the export endpoint itself are needed.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/research.py` — add `GET /api/research/briefs/export/capabilities` route
- **CREATE**: `frontend/src/components/ui/Toast.tsx` — reusable toast notification component
- **MODIFY**: `frontend/src/app/research/page.tsx` — add pagination controls, call capabilities API to disable PDF option with tooltip, replace inline `exportError` with Toast
- **MODIFY**: `frontend/src/lib/api.ts` — add `getExportCapabilities()` function
- **MODIFY**: `frontend/src/lib/types.ts` — add `ExportCapabilities` interface

---

### 3. Data Model

No new tables or columns. The `research_briefs` table from VO-361 is unchanged. The capabilities endpoint reads the module-level `REPORTLAB_AVAILABLE` flag already set in `backend/api/research.py`.

---

### 4. API Spec

**New endpoint only:**

```
GET /api/research/briefs/export/capabilities
Response 200:
{
  "formats": {
    "zip":  { "available": true },
    "csv":  { "available": true },
    "pdf":  { "available": false }   // false when REPORTLAB_AVAILABLE is False
  }
}
```

Existing `POST /api/research/briefs/export` — no changes. Existing `GET /api/research/briefs` pagination params (`page`, `page_size`) are already implemented on the backend; the frontend just needs to use them.

---

### 5. Frontend Component Spec

**Toast component** — `frontend/src/components/ui/Toast.tsx`
- Props: `message: string`, `variant: 'error' | 'info'`, `onDismiss: () => void`
- Fixed-position overlay (`bottom-4 right-4`), auto-dismisses after 5 s
- Used by `research/page.tsx` to surface export errors (404, 501, network)

**Changes to `frontend/src/app/research/page.tsx`:**

| Gap | Change |
|-----|--------|
| PDF availability | Call `getExportCapabilities()` on mount via `useApi`; disable `<option value="pdf">` and add `title="PDF export not available"` when `formats.pdf.available === false` |
| Pagination | Add `currentPage` state; render prev/next controls beneath the brief list; pass `page`/`page_size=25` to `getResearchBriefs()`; keep `selectedIds` as a `Set<number>` in component state so selections survive page changes |
| Error toast | Replace `exportError` inline `<div role="alert">` with `<Toast>` rendered at page root; keep 404 and 501 messages distinct |
| Partial select-all | Add `indeterminate` ref on the select-all `<input type="checkbox">` for the mixed-selection state |

**Renders on**: `frontend/src/app/research/page.tsx` (existing page, no new route needed)

---

### 6. Verification

1. **PDF disabled tooltip**: With `REPORTLAB_AVAILABLE = False` in `backend/api/research.py`, load the Research page, select any brief — confirm the PDF option in the format selector is disabled and hovering shows "PDF export not available".
2. **Cross-page selection**: Generate >25 briefs, navigate to page 2, select a brief, navigate back to page 1 — confirm the page 1 selections are still checked and the count badge reflects the cumulative total.
3. **100-brief limit + toast**: Select 101 briefs (use select-all across two pages), click Export — confirm the inline warning "Max 100 briefs per export" appears and the Export button remains disabled; then select exactly 100 and trigger export against a brief ID that was deleted — confirm a toast appears with the 404 message and no partial file is downloaded.
