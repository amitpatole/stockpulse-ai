# VO-329: Create batch export in research briefs

## User Story

## VO-383: Batch Export in Research Briefs

---

**User Story**

As a researcher, I want to select multiple research briefs and export them in a single action, so that I can efficiently compile and share findings without manually exporting one brief at a time.

---

**Acceptance Criteria**

- [ ] User can select multiple briefs via checkboxes in the briefs list view
- [ ] "Select All" / "Deselect All" toggle available when in selection mode
- [ ] Export button activates only when at least one brief is selected
- [ ] Supported export formats: PDF, CSV, JSON (at minimum PDF on day one)
- [ ] Exported briefs are bundled into a single ZIP archive named `research-briefs-export-{date}.zip`
- [ ] Each brief file inside the ZIP is named `{brief-title}-{id}.{ext}`
- [ ] Progress indicator shown during export generation (especially for large batches)
- [ ] Error handling: if one brief fails to export, the rest continue and user is notified of failures
- [ ] Maximum batch size of 100 briefs per export (with clear UI feedback if exceeded)
- [ ] Exported files preserve all metadata (timestamps, tags, source data references)

---

**Priority Reasoning**

Medium-high. Power users running multi-symbol research workflows are currently doing manual one-by-one exports — a known friction point. This directly reduces time-to-share for research outputs and is a low-risk, high-visibility feature. No new data models required.

---

**Estimated Complexity**

**3 / 5**

Backend ZIP bundling is straightforward. The main complexity is the selection state UI and graceful error handling for partial export failures. PDF rendering at scale may need async handling if briefs are large.

---

*Originated from Theo's feedback. Assign to backend + frontend pair.*
