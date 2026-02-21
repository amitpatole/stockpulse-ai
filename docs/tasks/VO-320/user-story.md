# VO-320: Add social sentiment badge to stock detail page

## User Story

# User Story: Social Sentiment Badge — Stock Detail Page

**ID**: VO-369
**Source**: Theo (internal feature request)

---

## User Story

> As a **trader using the stock detail page**, I want to **see a social sentiment badge reflecting current market buzz**, so that I can **factor crowd sentiment into my research without leaving the platform**.

---

## Acceptance Criteria

- [ ] Badge displays on the stock detail page header, adjacent to the stock ticker/price
- [ ] Sentiment rendered as one of three states: **Bullish**, **Bearish**, or **Neutral** with distinct color coding (green / red / gray)
- [ ] Badge shows a numeric sentiment score (e.g., 72/100) alongside the label
- [ ] Hovering the badge reveals a tooltip with source breakdown (e.g., Reddit mentions, StockTwits ratio, news tone)
- [ ] Data refreshes automatically every 5 minutes; badge shows a "stale" indicator if data is >15 minutes old
- [ ] Graceful degradation: if sentiment data is unavailable, badge displays "No data" — page does not error
- [ ] Sentiment score sourced from at least one real or mock external API (design should allow swapping providers)
- [ ] Mobile-responsive — badge remains legible on small viewports

---

## Priority Reasoning

**Medium-High.** Sentiment data is a meaningful differentiator for retail-focused trading tools. Low implementation risk (additive UI), high perceived value. Theo's instinct here is right — it's visible, shareable, and builds habit. Ships fast if we use a mock data layer first and wire real API later.

---

## Estimated Complexity

**3 / 5**

- Frontend badge component: straightforward
- Tooltip + stale state logic: moderate
- API integration + caching layer: the only real risk; scope-control with a mock initially
- No schema changes required

---

**Recommendation**: Build with mock data first, ship, validate engagement, then wire real sentiment API. Avoids blocking on API contracts.
