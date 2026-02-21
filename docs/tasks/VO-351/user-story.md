# VO-351: Pagination off-by-one in chart rendering list endpoint

## User Story

# User Story: VO-XXX — Fix Pagination Off-by-One in Chart Rendering List Endpoint

---

## User Story

**As a** trader reviewing historical chart data,
**I want** the chart list endpoint to return the correct page of results every time,
**so that** I never miss a chart or see a duplicate when paginating through large datasets.

---

## Acceptance Criteria

- [ ] Requesting page `N` with page size `K` returns items `[(N-1)*K, N*K)` — no off-by-one shift
- [ ] The last page returns only the remaining items (not an empty page or a repeated item from the previous page)
- [ ] Total item count and total page count in the response are accurate
- [ ] Edge cases pass: single item, exactly one full page, empty result set
- [ ] Existing chart rendering tests updated to assert correct pagination boundaries
- [ ] No regression in related list endpoints (watchlist, alerts)

---

## Priority Reasoning

**High.** Data integrity bugs erode user trust fast. A trader who can't trust the list they're looking at will question every screen in the app. This is also a shallow fix with outsized confidence value — ship it quickly.

---

## Estimated Complexity

**2 / 5** — Likely a single off-by-one in an offset/limit calculation. Fix is surgical; risk is low. The bulk of effort is test coverage to lock in the boundary conditions.
