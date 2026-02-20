# VO-030: Timezone display bug in chart rendering for non-US locales

## User Story

The existing VO-024/025 slots are taken. This timezone bug needs its own ticket. Here's the user story:

---

## VO-026: Timezone display bug in chart rendering for non-US locales

**Priority: P2 | Area: Chart Rendering | Found by: QA**

---

### User Story

As a **trader outside the US**, I want chart timestamps to display in my local timezone, so that I can accurately interpret when market events occurred without mentally converting from an assumed US timezone.

---

### Acceptance Criteria

- [ ] Chart x-axis timestamps render in the user's detected local timezone (browser `Intl` API), not hardcoded to US/Eastern or UTC
- [ ] Timestamps display correctly for at minimum: GMT, CET, JST, AEST, and IST locales
- [ ] Tooltip timestamps on hover match the same timezone as the x-axis labels
- [ ] Timezone label/indicator is visible on the chart (e.g. "15:30 CET") so users know what offset is applied
- [ ] No regression for US-based locales — existing behavior is preserved
- [ ] QA can reproduce the original bug scenario and confirm it no longer occurs across at least 3 non-US locales

---

### Priority Reasoning

**P2 — Medium-High.** This is a correctness bug that erodes trust for any non-US user — a significant and growing segment. A trader misreading a timestamp can make a bad decision. QA caught it, but it's almost certainly impacting users in production already. Not a crash, but meaningful enough to block a release targeting international users.

---

### Complexity: 2 / 5

Timezone rendering is a well-understood problem. The fix is almost certainly swapping hardcoded timezone references for `Intl.DateTimeFormat` or equivalent in the chart rendering layer. Scope is narrow (chart component + tooltip). Main risk is edge cases around DST transitions and any server-side timestamp formatting that may also be assuming US locale.

---

**Next step:** Assign to a frontend dev. Locate where chart timestamps are formatted — likely a single utility function. Confirm whether the bug is client-side only or also in API response formatting before estimating sprint placement.
