# VO-003: Add unit tests for technical analysis indicators

## User Story

Good. I've seen the code. Here's the user story:

---

## User Story: Unit Tests for Technical Analysis Indicators

**As a** backend engineer,
**I want** unit tests for the five pure indicator functions in `technical.py`,
**so that** regressions in trading signal logic are caught before they reach production and affect user decisions.

---

### Acceptance Criteria

- [ ] Test file at `backend/agents/tools/test_technical.py` (or `tests/` mirror)
- [ ] Synthetic OHLCV data fixtures — no network calls, no external dependencies
- [ ] **Bollinger Bands** (`calculate_bollinger_bands`):
  - Correct upper/middle/lower math for flat and trending series
  - `signal` returns `overbought` when price > upper band
  - `signal` returns `oversold` when price < lower band
  - Returns `error` dict when data length < `period`
- [ ] **ATR** (`calculate_atr`):
  - True range computed correctly across gap-up/gap-down scenarios
  - Volatility label thresholds (`low`, `moderate`, `high`, `very_high`) match documented cutoffs
  - Returns `error` dict when data length < `period + 1`
- [ ] **VWAP** (`calculate_vwap`):
  - Weighted average math verified against hand-calculated expected value
  - `signal` is `bullish` when current price > VWAP, `bearish` when below
  - Handles zero-volume bars without crashing
- [ ] **OBV** (`calculate_obv`):
  - Accumulates correctly on up days, decrements on down days, holds on flat
  - `obv_trend` is `accumulation` / `distribution` / `neutral` based on last 5 values
  - Returns `error` dict when fewer than 2 data points
- [ ] **Stochastic** (`calculate_stochastic`):
  - `%K` is 100 when close equals highest high
  - `%K` is 0 when close equals lowest low
  - `signal` is `overbought` when `%K > 80`, `oversold` when `%K < 20`
  - Returns `error` dict when data length < `k_period`
- [ ] All tests pass with `pytest` and no mocking of external services

---

### Priority Reasoning

These are pure math functions feeding AI agent outputs that users rely on for trading decisions. A silent regression (e.g., wrong std dev divisor, off-by-one true range) produces incorrect buy/sell signals with zero feedback. Since we have **zero test coverage today**, this is the highest-leverage starting point — isolated, deterministic, and fast to write.

---

### Complexity: **2 / 5**

Functions are stateless and dependency-free — tests require only list arithmetic and `pytest`. No DB, no API mocking, no async handling. Straightforward to parallelize across all five indicators once fixture data is defined.
