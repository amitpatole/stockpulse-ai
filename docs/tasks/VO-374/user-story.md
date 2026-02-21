# VO-374: Missing input validation in price alert notifications allows injection

## User Story

## User Story: VO-XXX — Input Validation for Price Alert Notifications

---

### User Story

**As a** platform user who sets price alerts,
**I want** my alert inputs (ticker symbols, price thresholds, notification messages) to be validated and sanitized before processing,
**so that** malicious actors cannot inject harmful payloads through alert fields that get rendered in notifications or stored in the database.

---

### Acceptance Criteria

- [ ] All user-supplied alert fields (symbol, threshold values, alert name/description) are validated server-side before persistence — client-side validation alone is insufficient
- [ ] Ticker symbols are validated against an allowlist pattern (e.g., `^[A-Z]{1,5}$`); invalid symbols are rejected with a clear 400 error
- [ ] Numeric threshold fields (`price_above`, `price_below`, `pct_change`) reject non-numeric input and enforce sane min/max bounds
- [ ] Free-text fields (alert names, notes) are stripped of HTML/script tags before storage and before inclusion in SSE payloads
- [ ] SSE notification payloads are JSON-encoded (not string-interpolated) to prevent injection via notification content
- [ ] Existing alerts with potentially unsafe stored values are sanitized on read before being sent over SSE
- [ ] Validation errors return structured error responses — no raw exception messages leaked to the client
- [ ] All validation logic has unit test coverage for boundary cases and known injection vectors (XSS strings, SQL metacharacters, oversized inputs)

---

### Priority Reasoning

**High.** This is a security vulnerability, not a UX issue. SSE payloads rendered client-side with unsanitized content are a direct XSS vector. Price alerts are user-facing, high-frequency, and touch both the database and real-time notification pipeline — two injection surfaces. Ship before the next release.

---

### Estimated Complexity

**2 / 5** — Validation logic is well-understood. The risk is in coverage (finding every injection surface), not in implementation difficulty. Regex allowlisting + JSON serialization discipline + a sanitizer library gets this done cleanly. Main effort is writing the test cases.
