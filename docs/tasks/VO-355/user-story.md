# VO-355: Support batch export in research briefs

## User Story

The backend export endpoint already exists from VO-361 (`POST /api/research/briefs/export` supporting ZIP/CSV/PDF up to 100 briefs). The gap is the frontend — no UI to select and trigger the export.

Here's the user story:

---

## VO-XXX: Batch Export Research Briefs

### User Story

**As a** power user managing research briefs, **I want** to select multiple briefs and export them in bulk as ZIP, CSV, or PDF, **so that** I can archive, share, or process research output offline without downloading briefs one at a time.

---

### Acceptance Criteria

- A checkbox appears on each brief row in the research briefs list; a "select all" checkbox controls the full visible page
- A toolbar appears when ≥1 brief is selected, showing the count and an **Export** button with format options (ZIP / CSV / PDF)
- Selecting ZIP downloads a `.zip` of individual text files (one per brief); CSV downloads a flat spreadsheet; PDF downloads a single combined document
- Export is limited to 100 briefs per batch — selecting more shows an inline error, not a silent failure
- Duplicate IDs in the selection are silently deduplicated; export order matches selection order
- If PDF export is unavailable server-side, the PDF option is disabled in the UI with a tooltip: "PDF export not available"
- Brief IDs not found in the DB return a 404 with a user-visible error toast — no partial silent exports
- Selecting briefs across pages is supported (selection state persists during pagination)
- Export filename format: `research-brief-export-YYYY-MM-DD.{ext}`

---

### Priority Reasoning

**Medium.** The backend is fully built (VO-361). This is pure frontend work with a working API contract. High utility for analysts who run regular research batches — reduces friction for a workflow that currently requires one-by-one handling. Not blocking any other work; ship when bandwidth allows.

---

### Estimated Complexity

**2 / 5**

- Backend: zero changes needed — endpoint is production-ready
- Frontend: checkbox selection state, toolbar component, `fetch` call to existing endpoint, file download trigger
- Main risk: cross-page selection state management if using a paginated list without a global store
