# VO-391: Screen reader accessibility issue in SSE event streaming

## User Story

# VO-387: Screen Reader Accessibility — SSE Event Streaming

---

## User Story

**As a** visually impaired trader using a screen reader,
**I want** real-time SSE updates (price alerts, market data changes, news feed) to be announced by my assistive technology,
**so that** I can trade and monitor positions without relying on visual cues.

---

## Acceptance Criteria

- [ ] SSE events delivered to the frontend trigger an ARIA live region update (`aria-live="assertive"` for alerts, `aria-live="polite"` for routine market data)
- [ ] Price alert SSE events announce the alert type, ticker symbol, and triggered price (e.g., "Price alert: AAPL crossed above $195.00")
- [ ] News feed updates do not interrupt time-sensitive alert announcements (priority ordering respected)
- [ ] Screen reader announcements do not duplicate — if an SSE event fires multiple times in quick succession, only one announcement is made (debounce ≤ 500ms)
- [ ] SSE connection status changes (connected, reconnecting, disconnected) are announced once per state transition
- [ ] All ARIA live region containers are present in the DOM on initial page load, not injected dynamically
- [ ] Verified against NVDA + Firefox and VoiceOver + Safari

---

## Priority Reasoning

**Priority: High**

WCAG 2.1 AA compliance is a legal baseline, not a nice-to-have. SSE is the primary real-time data channel — if it's silent to screen readers, the core product value is inaccessible. Any user with a visual impairment cannot act on alerts. Reputational and legal exposure justifies immediate attention.

---

## Estimated Complexity: **3 / 5**

Backend SSE payloads are unchanged. Work is frontend-only: ARIA live region wiring, debounce logic, and message formatting. No schema or API changes needed. Testing surface (multiple screen reader/browser combos) is the main complexity driver.
