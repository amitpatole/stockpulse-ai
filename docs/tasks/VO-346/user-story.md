# VO-346: Support performance comparison mode in stock detail page

## User Story

Here's the user story for Theo's feature idea:

---

## VO-396: Performance Comparison Mode — Stock Detail Page

### User Story

**As a** trader on the stock detail page,
**I want** to overlay the performance of additional stocks and benchmarks on the price chart,
**so that** I can quickly judge relative strength without switching tabs or opening a separate tool.

---

### Acceptance Criteria

- [ ] A "Compare" button/input on the stock detail page allows the user to add up to 4 comparison symbols (tickers or benchmarks like SPY, QQQ)
- [ ] Added symbols are plotted as normalized % return lines on the existing price chart (rebased to 0% at the selected start of the time range)
- [ ] Each comparison line has a distinct color with a legend entry showing symbol + current % return delta
- [ ] Comparison symbols persist across time range changes (1D, 1W, 1M, 1Y) — chart rebases automatically
- [ ] Symbols can be individually removed via a close/X on each legend chip
- [ ] If a comparison symbol is invalid or has no data for the selected range, a non-blocking inline warning is shown and that symbol is skipped
- [ ] Comparison state is reflected in the URL (e.g., `?compare=SPY,MSFT`) for shareability
- [ ] No degradation to existing single-stock chart performance or load time

---

### Priority Reasoning

**Medium.** Core stock detail page works, but comparison is table-stakes for any research workflow — traders constantly benchmark against SPY or peer stocks. Theo's instinct is right; this meaningfully increases session depth and retention on a high-traffic page. Not a blocker for anything, but high user value relative to effort.

---

### Estimated Complexity

**3 / 5** — Chart overlay logic and normalization are non-trivial but well-understood. Requires a new multi-symbol data endpoint (or batching existing calls), frontend chart layer changes, and URL state management. No schema changes. Main risk is chart library abstraction — needs a spike if the current charting lib doesn't support multi-series well.
