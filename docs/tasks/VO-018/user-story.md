# VO-018: Pagination off-by-one in settings page list endpoint

## User Story

Done. Here's the summary:

---

**VO-018: Pagination off-by-one in settings page list endpoint**

**User story:** As a user browsing paginated lists in the settings page, I want each page to show the correct items in the correct order, so that I never miss an item or see the same item twice due to a pagination boundary error.

**Key acceptance criteria:**
- Correct items on every page — no skipped or duplicated items at boundaries
- `has_next` is accurate, including when `total` is exactly divisible by `page_size`
- Consistent `(page - 1) * page_size` offset formula across all settings list endpoints
- Regression tests covering exact-boundary cases

**Priority: P2.** Data correctness bug, not a crash. Confusing to users but not blocking. Fix this sprint before it ships, after P1 work.

**Complexity: 2/5.** One-line arithmetic fix. Effort is mostly in writing the boundary-case regression tests.
