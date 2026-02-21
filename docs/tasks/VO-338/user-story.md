# VO-338: Timezone display bug in data provider fallback chain for non-US locales

## User Story

Here's the user story, filed as **VO-336** (next in sequence after VO-335):

---

## VO-336: Timezone Display Bug — Data Provider Fallback Chain (Non-US Locales)

**User Story**

> As a **trader or analyst using Virtual Office from a non-US locale** (India, EU, Japan, Australia), I want **all market data timestamps correctly normalized to UTC before being served**, so that **I can trust timestamps for quotes, historical prices, and agent events — and convert them to my local time without off-by-hours errors**.

---

**Acceptance Criteria**

- All `datetime.fromtimestamp(ts)` calls in every provider updated to include `tz=timezone.utc`
- All `datetime.utcnow()` replaced with `datetime.now(timezone.utc)` across the backend
- All `datetime.utcfromtimestamp()` replaced with `datetime.fromtimestamp(..., tz=timezone.utc)`
- All JSON-serialized datetimes include explicit UTC offset (ISO8601 with `+00:00` or `Z`), never naive strings
- The same Unix timestamp through any fallback provider yields the identical UTC datetime
- Existing `test_data_provider_fallback.py` tests continue to pass
- New tests assert returned datetimes are timezone-aware (`tzinfo is not None`)
- QA validates correct display in at least two non-US locales (IST +05:30, CET +01:00)

---

**Priority: High.** Data correctness in a trading app. Off-by-hours timestamps can directly affect trading decisions. Affects all non-US users, worsens under fallback (each provider independently applies the same broken conversion). Low regression risk.

**Complexity: 2/5.** Mechanical find-and-replace of ~20+ deprecated/naive datetime calls. No schema changes, no API contract changes. A grep pass before and after verifies completeness. ~4 hours total including QA.

---

Saved to `docs/tasks/VO-336/user-story.md`.
