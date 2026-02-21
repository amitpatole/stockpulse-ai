# VO-316: Add earnings calendar widget to market overview dashboard

## User Story

# VO-XXX: Earnings Calendar Widget — Market Overview Dashboard

---

## User Story

**As a** trader using the market overview dashboard,
**I want** to see upcoming earnings announcements for stocks I'm tracking,
**so that** I can anticipate volatility and position my trades ahead of major events.

---

## Acceptance Criteria

- [ ] Widget displays upcoming earnings events for the next 7 days by default (configurable: 7/14/30 days)
- [ ] Each entry shows: ticker symbol, company name, expected report date, report timing (BMO/AMC/unconfirmed), and EPS estimate if available
- [ ] Entries are sorted chronologically; ties broken alphabetically by ticker
- [ ] Clicking a ticker navigates to the stock detail page
- [ ] Widget updates daily (not real-time); stale data older than 24h is visually flagged
- [ ] Empty state shown clearly when no earnings fall in the selected window
- [ ] Widget is responsive — degrades gracefully on narrow layouts
- [ ] Data source and last-updated timestamp visible in widget footer
- [ ] Widget can be dismissed/minimized like other dashboard widgets

---

## Priority Reasoning

**Medium-High.** Earnings events are the single biggest short-term volatility driver for equities. Users currently have no in-app signal for this — they're leaving the product to check external calendars. Keeping them in-app increases session depth and positions Virtual Office as a one-stop research tool. Low operational risk (read-only, daily refresh).

---

## Estimated Complexity

**3 / 5**

- Data sourcing is the main unknown — need to confirm API availability/cost
- Frontend widget is straightforward given existing dashboard component patterns
- No write operations, no real-time requirements
- Scope risk: EPS estimates may require a paid data tier; ship without them in v1 if blocked

---

**Owner:** Theo (feature req) — assign to frontend + backend pair
**Depends on:** Earnings data API selection (spike required before sprint commit)
