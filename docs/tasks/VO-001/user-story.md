# VO-001: Add stock detail page with multi-timeframe charts

## User Story

# User Story: Stock Detail Page

## User Story
As a **trader using the Virtual Office dashboard**, I want a **dedicated stock detail page with charts, key stats, and news**, so that I can **do deep-dive analysis on any stock without leaving the app**.

---

## Acceptance Criteria

**Navigation**
- [ ] Stock name/ticker in `StockGrid.tsx` is clickable and routes to `/stock/[ticker]`
- [ ] Page loads with ticker from URL, handles invalid tickers with a clear error state

**Chart**
- [ ] TradingView Lightweight candlestick chart renders OHLCV data
- [ ] Timeframe selector (1D, 1W, 1M, 3M, 1Y) updates chart data on click
- [ ] Active timeframe is visually highlighted

**Key Stats Sidebar**
- [ ] Displays: current price, % change, volume, market cap, 52w high/low, P/E ratio, EPS
- [ ] Data sourced from yfinance via new backend endpoint
- [ ] Values update on page load (no stale data)

**Technical Indicators**
- [ ] Shows current RSI value with overbought/oversold callout (>70 / <30)
- [ ] Shows MACD signal (bullish/bearish)
- [ ] Shows Bollinger Band position (upper/mid/lower band proximity)

**News Feed**
- [ ] Displays recent news filtered to the viewed ticker
- [ ] Uses existing news API — no new integration required
- [ ] Shows headline, source, and timestamp

**Backend**
- [ ] `GET /api/stocks/<ticker>/detail` returns quote + indicators + news in a single aggregated response
- [ ] Returns meaningful error for unknown tickers (404)

---

## Priority Reasoning

**High priority.** The stock grid is currently a dead end — users see data but can't drill in. This closes the loop on the core workflow: *scan → investigate → decide*. It's the feature most likely to drive daily active usage and session depth.

---

## Estimated Complexity

**4 / 5**

Multiple moving parts: new frontend route + layout, TradingView chart integration, aggregated backend endpoint, yfinance data mapping, and wiring three distinct data sources (quote, indicators, news) into one cohesive page. Individually straightforward; coordination cost is the risk.

---

**Suggested scope cut if needed:** Ship without technical indicators in v1 — chart + stats + news delivers 80% of the value. Indicators can follow in a fast-follow.
