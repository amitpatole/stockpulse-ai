# VO-380: Timezone display bug in chart rendering for non-US locales

## User Story

# VO-XXX: Timezone Display Bug in Chart Rendering (Non-US Locales)

---

## User Story

**As a** trader or analyst using Virtual Office from a non-US timezone (e.g., London, Tokyo, Sydney),
**I want** stock chart time axes to display timestamps in my local timezone (or a clearly labeled market timezone),
**so that** I can accurately interpret price action relative to market hours without mentally converting from US Eastern time.

---

## Acceptance Criteria

- [ ] Chart x-axis timestamps render in the user's browser-detected timezone by default
- [ ] A timezone label is displayed on the chart (e.g., "Times shown in: Europe/London")
- [ ] Market open/close overlay markers (if present) align correctly with the displayed timezone
- [ ] Switching between timeframes (1D, 1W, 1M, etc.) preserves the correct timezone rendering
- [ ] No regression for US-based users — EST/EDT charts remain unaffected
- [ ] Cross-browser tested: Chrome, Firefox, Safari on both US and non-US locale settings
- [ ] Edge case: UTC+0 and UTC- timezones render without sign/offset errors

---

## Priority Reasoning

**Priority: High**

This is a data accuracy issue, not a cosmetic one. Traders making time-sensitive decisions based on misaligned chart timestamps face real financial risk. It also signals lack of international readiness, which blocks any future expansion beyond US users. QA catching this before production release is lucky — it needs to ship fixed.

---

## Estimated Complexity

**3 / 5**

Timezone handling in JS is well-understood (Intl API / date-fns-tz / day.js), but chart library integration (likely Chart.js or similar) may require custom tick formatting callbacks. The multi-timeframe toggle (recently shipped in VO-327) adds a regression surface that needs validation. Not trivial, but well-scoped.
