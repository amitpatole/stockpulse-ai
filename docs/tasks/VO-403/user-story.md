# VO-403: Timezone display bug in stock detail page for non-US locales

## User Story

## VO-XXX: Timezone Display Bug — Stock Detail Page (Non-US Locales)

---

### User Story

**As a** non-US trader using Virtual Office, **I want** timestamps on the stock detail page to display in my local timezone (or a clearly labeled timezone), **so that** I can accurately interpret market events, price movements, and news without mentally converting from US Eastern time.

---

### Acceptance Criteria

- All timestamps on the stock detail page (last trade, price history, news feed, earnings dates) display the timezone label explicitly (e.g., `14:32 CET`, not bare `14:32`)
- Users with a non-US browser locale see timestamps converted to their system timezone by default
- A timezone indicator/toggle is visible on the page — users can switch between local time and market time (ET)
- No timestamps display as `NaN`, `Invalid Date`, or raw UTC strings for any locale
- Existing US-locale behavior is unchanged — regression-free
- Timezone conversion handles DST transitions correctly (US and non-US)
- Server-sent timestamps are always ISO 8601 with explicit UTC offset — no ambiguous bare strings from the API

---

### Priority Reasoning

**High.** This is a correctness bug, not a cosmetic one. A trader misreading a timestamp by hours can make a bad trade. As we expand outside the US market, this is a trust and retention issue — first impressions for international users are broken. QA caught it now; we ship the fix before it hits production.

---

### Estimated Complexity

**3 / 5**

- API audit needed to confirm all endpoints return timezone-aware timestamps
- Frontend date formatting likely needs a centralized utility (replace ad-hoc `new Date()` calls)
- DST edge cases require careful testing
- No schema changes expected
