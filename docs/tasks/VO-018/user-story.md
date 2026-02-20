# VO-018: Pagination off-by-one in settings page list endpoint

## User Story

**VO-018 | Settings Page | P2**

---

### User Story

As a **user browsing paginated lists in the settings page**, I want each page to show the correct items in the correct order, so that I never miss an item or see the same item twice due to a pagination boundary error.

---

### Acceptance Criteria

- [ ] The first page returns items 1–N (no item skipped, no fence-post error at the boundary)
- [ ] The last page returns only the remaining items — no empty final page and no item repeated from the previous page
- [ ] `has_next` is `true` if and only if there are items beyond the current page
- [ ] `has_next` returns `false` when `total` is exactly divisible by `page_size` and the user is on the last page
- [ ] Page offset calculation uses `(page - 1) * page_size` — 1-based page numbers correctly converted to 0-based DB offsets
- [ ] All list endpoints in the settings page area use the same, consistent pagination formula
- [ ] A regression test is added covering exact-boundary cases: `total == page_size`, `total == 2 * page_size`, `total == page_size + 1`

---

### Priority Reasoning

**P2 — Medium.** This is a data-correctness bug caught by QA, not a crash. Users browsing settings lists will silently miss items or see a phantom empty last page — confusing but not blocking. It should be fixed this sprint before it reaches production, but it doesn't outrank P1 stability work.

---

### Complexity Estimate

**2 / 5**

Off-by-one pagination bugs follow a well-known pattern. The fix is a one-line arithmetic correction to the `has_next` check. The regression tests add the majority of the effort. Low risk, contained scope.

---

**Next step:** Assign to a dev. Point them at the settings page list endpoint and the `has_next` calculation. Require boundary-case tests before merge.
