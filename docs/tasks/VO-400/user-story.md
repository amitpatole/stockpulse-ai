# VO-400: Pagination off-by-one in settings persistence list endpoint

## User Story

## VO-362: Pagination Off-by-One in Settings Persistence List Endpoint

---

### User Story

**As a** power user managing multiple saved settings configurations,
**I want** the settings list endpoint to return the correct page of results with accurate pagination metadata,
**so that** I can reliably navigate through my settings without missing items or seeing duplicates.

---

### Acceptance Criteria

- [ ] Requesting page `N` with page size `K` returns items `[(N-1)*K, N*K)` — not `[(N-1)*K+1, N*K]` or any other off-by-one variant
- [ ] The `total_pages` field in the response correctly reflects `ceil(total_items / page_size)`
- [ ] The last page returns only the remaining items (not an empty page or a repeated item)
- [ ] Requesting a page beyond `total_pages` returns an empty results list with a `400` or `404`, not a server error
- [ ] `has_next` and `has_prev` flags (if present) are accurate for boundary pages (first and last)
- [ ] Existing settings are not omitted or duplicated across pages at any page size (1, 10, 100)
- [ ] Regression test covers: single item, exact-multiple, and non-multiple total counts

---

### Priority Reasoning

**Medium-High.** Data integrity bug — users lose trust when list views silently drop or repeat records. Settings persistence is core infrastructure; if pagination is broken here it likely affects other list endpoints. Not blocking core trading flows, but will surface immediately to any user with more than one page of saved settings.

---

### Estimated Complexity

**2 / 5** — Almost certainly a one-line fix (wrong `OFFSET` or `LIMIT` calculation in the query, or a fence-post error in the page math). Testing the boundary cases adds the bulk of the work.
