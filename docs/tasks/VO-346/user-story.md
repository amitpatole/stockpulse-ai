# VO-346: Support performance comparison mode in stock detail page

## User Story

# User Story: Performance Comparison Mode

**VO-XXX** | Feature | Theo's Idea

---

## User Story

As a **trader**, I want to overlay multiple stocks on a single performance chart in the stock detail page, so that I can quickly assess relative performance without switching between tabs or building manual comparisons elsewhere.

---

## Acceptance Criteria

**Core Behavior**
- User can add up to 4 comparison tickers via a search/input field on the stock detail page
- All compared assets are normalized to a common baseline (% change from period start, not raw price)
- Each ticker renders as a distinct colored line with a legend
- Comparison tickers persist for the session but do not override the primary stock context

**Chart Interactions**
- Existing time range selector (1D, 1W, 1M, 3M, 1Y) applies to all overlaid tickers simultaneously
- Tooltip shows all ticker values at the hovered timestamp
- User can remove individual comparison tickers via an X on the legend

**Data & Performance**
- Comparison data loads in parallel, not sequentially
- Graceful degradation if a comparison ticker fails to load (skip it, show error badge on legend)
- No regression to existing single-stock chart behavior

**Edge Cases**
- Duplicate tickers silently ignored
- Comparing a ticker to itself is a no-op
- Input validates against known tickers; unknown tickers show an inline error

---

## Priority Reasoning

**Medium-High.** Comparison is table-stakes for any serious trading research tool — users are doing this manually today by opening multiple tabs. High engagement feature with low churn risk. Unblocks more advanced features (correlation analysis, portfolio overlay) later. Ship it before a competitor does.

---

## Estimated Complexity

**3 / 5**

Chart overlay logic and normalization are non-trivial but well-understood. The main risk is parallel data fetching and keeping the UI clean with 4+ tickers. No new backend endpoints likely needed if price history API already supports arbitrary tickers. Frontend carries most of the weight here.
