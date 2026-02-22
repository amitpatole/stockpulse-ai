# VO-352: Create earnings calendar widget in market overview dashboard

## User Story

# User Story: Earnings Calendar Widget

**VO-362 | Feature | Market Overview Dashboard**

---

## User Story

As a **trader using the market overview dashboard**, I want an **earnings calendar widget showing upcoming company earnings releases**, so that **I can anticipate potential volatility and position my research accordingly before key announcements**.

---

## Acceptance Criteria

**Display**
- Widget shows earnings events for the next 7 days by default (configurable: 1d, 7d, 30d)
- Each entry shows: ticker, company name, date/time, EPS estimate, and before/after market indicator (BMO/AMC)
- Entries are sorted chronologically; past events visually dimmed
- Empty state handled gracefully ("No earnings this week")

**Interaction**
- Clicking a ticker navigates to the stock detail page
- Widget is scrollable if events exceed visible area
- User can filter by watchlist tickers only (toggle)

**Data**
- Data sourced from existing market data pipeline or a dedicated earnings endpoint
- Refreshes automatically on dashboard load; manual refresh button available
- Stale data (>1hr old) shows a warning indicator

**Integration**
- Widget fits the existing dashboard grid layout without breaking responsive behavior
- Follows established widget styling/theming conventions

**Error Handling**
- Displays inline error if data fetch fails (no full-page crash)

---

## Priority Reasoning

**Medium-High.** Earnings are the single highest-volatility event for any stock. Traders who miss earnings dates make uninformed decisions. This is low-friction, high-visibility value — it surfaces on the dashboard every session. Theo's instinct is right; competing platforms (Bloomberg, Finviz) all lead with this.

Ship after any open P0/P1 bugs are clear.

---

## Complexity Estimate

**3 / 5**

- UI is straightforward (table/list widget, existing patterns to follow)
- Main complexity is the data layer: sourcing reliable earnings data, deciding on refresh cadence, and handling the before/after market distinction cleanly
- Watchlist filter requires cross-widget state awareness
