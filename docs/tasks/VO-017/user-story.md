# VO-017: Null reference in settings page when user has no data

## User Story

## User Story: Settings Page Null Reference — No Data State

**VO-BUG-001 | Settings Page | P1**

---

### User Story

As a **new or data-sparse user**, I want the settings page to load without crashing, so that I can configure my preferences regardless of whether I have existing data.

---

### Acceptance Criteria

- [ ] Settings page renders successfully when user has zero data (no trades, no watchlists, no history)
- [ ] All settings sections display a valid empty/default state instead of throwing a null reference error
- [ ] No unhandled exceptions or blank screens occur during page load for any user account state
- [ ] Default values are used as fallback when user data fields are null or undefined
- [ ] Error is not surfaced to the user — silent graceful degradation
- [ ] Regression test added covering the null-data user scenario

---

### Priority Reasoning

**P1 — High.** This is a crash-level bug discovered by QA, which means it will hit real users. Settings pages are accessed frequently, especially during onboarding when users are most likely to have no data. A broken settings page erodes trust immediately.

---

### Complexity Estimate

**2 / 5**

Likely a missing null check or unguarded data access in the settings page component. Low surface area, well-scoped fix. The defensive coding pattern is straightforward; the regression test adds a small amount of overhead.

---

**Next step:** Assign to a dev, point at the settings page component, and get it closed this sprint. No reason this lingers.
