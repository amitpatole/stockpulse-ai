# VO-387: Screen reader accessibility issue in research brief export

## Technical Design

---

### 1. Approach

All changes are confined to `frontend/src/app/research/page.tsx` — additive ARIA attribute changes only. A computed `aria-label` on the export button will reflect the dynamic count and format. A visually-hidden `aria-live="polite"` region will announce selection count changes, and the error container will gain `role="alert"` so errors are immediately announced without a separate `aria-live` attribute.

---

### 2. Files to Create/Modify

- **MODIFY**: `frontend/src/app/research/page.tsx` — add `aria-label` computation for export button, `role="toolbar"` + `aria-label` on toolbar wrapper, `role="alert"` on error container, `aria-live` selection-count region, and `aria-pressed` on icon-button checkboxes

No other files require changes. No new files.

---

### 3. Data Model

No database changes. Accessibility attributes are purely frontend.

---

### 4. API Spec

No new endpoints. No backend changes.

---

### 5. Frontend Component Spec

**Component**: Inline JSX in `ResearchPage` — `frontend/src/app/research/page.tsx`

**Changes by element:**

**Export button** (lines ~258–274): Add a computed `aria-label` derived from state:
```ts
const exportAriaLabel = exporting
  ? 'Exporting, please wait'
  : selectedIds.size === 0
    ? 'Export briefs, none selected'
    : `Export ${selectedIds.size} brief${selectedIds.size === 1 ? '' : 's'} as ${exportFormat.toUpperCase()}`;
```
Apply as `aria-label={exportAriaLabel}` on the `<button>`. Existing `disabled` prop already satisfies the disabled-state criterion.

**Toolbar wrapper div** (line ~248): Add `role="toolbar"` and `aria-label="Batch export"` to the outer `<div>`.

**Error container** (wherever `exportError` renders): Add `role="alert"` to the wrapping element. Remove any redundant `aria-live` if present — `role="alert"` implies `aria-live="assertive"`.

**Selection count live region** — add a visually-hidden span immediately outside the toolbar's conditional block (always rendered, never hidden, so the live region is registered before the count changes):
```tsx
<span
  className="sr-only"
  aria-live="polite"
  aria-atomic="true"
>
  {selectedIds.size > 0 ? `${selectedIds.size} brief${selectedIds.size === 1 ? '' : 's'} selected` : ''}
</span>
```

**Icon-button checkboxes** — select-all (line ~226) and per-brief (line ~324): Add `aria-pressed={allSelected}` / `aria-pressed={selectedIds.has(brief.id)}` respectively. This communicates toggled state to screen readers without converting to native `<input type="checkbox">`.

**No regressions**: existing `aria-label="Export format"` on the `<select>` and per-brief `aria-label` on checkboxes are untouched.

---

### 6. Verification

1. **VoiceOver/NVDA on export button**: Tab to the button with 2 briefs selected and ZIP format chosen — screen reader announces `"Export 2 briefs as ZIP, button"`. Click export — announces `"Exporting, please wait"`. Deselect all — button announces disabled state.

2. **Selection count live region**: Check/uncheck brief checkboxes with a screen reader active — each toggle announces `"N briefs selected"` without focus moving.

3. **Error announcement**: Trigger an export failure (e.g., disconnect network) — screen reader immediately announces the error text without user interaction, confirming `role="alert"` fires assertively.
