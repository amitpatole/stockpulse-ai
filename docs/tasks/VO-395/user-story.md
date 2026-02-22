# VO-395: Edge case in stock detail page when input is empty

## User Story

## User Story: VO-362 — Empty Input Edge Case on Stock Detail Page

---

### User Story

**As a** trader using the stock detail page,
**I want** the app to handle empty or blank ticker input gracefully,
**so that** I don't encounter crashes, broken UI states, or confusing error messages that interrupt my workflow.

---

### Acceptance Criteria

- [ ] Submitting an empty or whitespace-only ticker input does **not** trigger an API call or navigation
- [ ] An inline validation message is displayed (e.g., "Please enter a ticker symbol") when the user attempts to submit empty input
- [ ] The input field is focused and highlighted on invalid submission — no page reload or route change occurs
- [ ] If the stock detail page is loaded directly via URL with an empty/missing ticker param, the user is redirected to the search/home page with a toast notification
- [ ] No console errors or unhandled exceptions are thrown for any empty input scenario
- [ ] Behavior is consistent across keyboard (Enter key) and mouse (submit button) submission paths

---

### Priority Reasoning

**High.** This is a QA-caught regression on a core user flow — the stock detail page is the primary value surface. Empty input edge cases are low effort to fix but create a poor first impression and can mask deeper validation gaps. Ship it fast.

---

### Estimated Complexity

**2 / 5** — Input validation + guard clause on the API call + a redirect handler for direct URL access. No schema changes. Likely touches 1–2 frontend files and possibly one route guard.
