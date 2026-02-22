# VO-328: Add batch export to research briefs

## User Story

# User Story: Batch Export for Research Briefs

---

## User Story

**As a** quantitative researcher using Virtual Office,
**I want** to select multiple research briefs and export them together in a single action,
**so that** I can efficiently compile and share research packages without manually exporting one brief at a time.

---

## Acceptance Criteria

- [ ] User can select multiple research briefs via checkboxes in the briefs list view
- [ ] A "Export Selected" action appears when one or more briefs are selected
- [ ] Supported export formats: PDF (bundled), ZIP (individual files), CSV (metadata + summaries)
- [ ] Export respects the current filtered/sorted view — only selected items are included
- [ ] User receives a single downloadable file upon completion
- [ ] Export includes brief title, date, author, tags, and full content
- [ ] Empty selection state is handled gracefully (button disabled, tooltip explains)
- [ ] Export progress is indicated for large batches (>10 briefs)
- [ ] Exported filenames follow a consistent convention: `research-brief-export-YYYY-MM-DD.zip`

---

## Priority Reasoning

**Medium-High.** Research briefs are a core output of the platform. Batch export directly reduces friction in the researcher → stakeholder workflow. Theo flagging this suggests active user pain — if power users are requesting it, it's blocking real usage. Low risk, high perceived value.

---

## Complexity Estimate

**3 / 5**

- Selection UI is straightforward
- PDF bundling adds moderate complexity (pagination, consistent styling)
- ZIP packaging is simple
- No backend schema changes required — reads existing data
- Main risk: PDF rendering performance at scale
</s>
