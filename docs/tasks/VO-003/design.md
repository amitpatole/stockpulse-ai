# VO-003: Add unit tests for technical analysis indicators

## Technical Design

## Technical Design Spec: Unit Tests for `technical.py`

---

### 1. Approach

Write a single `pytest` test module targeting the five standalone pure functions. No mocking, no fixtures beyond in-module list literals. The functions depend only on `math` (stdlib), so tests run with zero setup. One `conftest.py` at the `backend/` root to ensure the package is importable without installing the full app.

Key implementation notes from reading the source:
- Bollinger Bands uses **population variance** (`/ period`, not `/ period - 1`) — hand-calc must match this.
- ATR error guard is `len(closes) < period + 1` (needs at least 15 points for default period=14).
- VWAP skips bars where `v == 0` entirely (`continue`) — zero-volume rows are safe.
- OBV trend compares `recent[-1]` vs `recent[0]` from a trailing-5 window.
- Stochastic `%K = 100` when `close == highest_high`, `%K = 0` when `close == lowest_low`.

---

### 2. Files to Create/Modify

| Action | Path |
|--------|------|
| **Create** | `backend/agents/tools/test_technical.py` |
| **Create** | `backend/conftest.py` (empty, makes `backend` importable as a package root) |

No existing files are modified.

---

### 3. Data Model Changes

None. These are pure functions — no DB, no state.

---

### 4. API Changes

None.

---

### 5. Frontend Changes

None.

---

### 6. Testing Strategy

**Framework:** `pytest` (stdlib assertions, no mocking libraries needed)

**Structure:** One test class per function, each containing 3–5 focused test methods.

| Class | Key test cases |
|-------|---------------|
| `TestBollingerBands` | Flat series math (upper=middle=lower when std=0); trending series hand-calc; `signal="overbought"` when price > upper; `signal="oversold"` when price < lower; `error` dict when `len < period` |
| `TestATR` | Gap-up true range (uses `abs(high - prev_close)`); gap-down true range; volatility label boundaries (construct series whose ATR% sits at 1.5/2.5/4.0 thresholds); `error` dict when `len < period + 1` |
| `TestVWAP` | Hand-calculated 3-bar expected value; `signal="bullish"` when close > vwap; `signal="bearish"` when close < vwap; all-zero volume bars (no crash, returns vwap=0) |
| `TestOBV` | Up-day accumulates volume; down-day decrements; flat day holds; 6-bar rising series → `obv_trend="accumulation"`; 6-bar falling → `"distribution"`; `error` dict when `len < 2` |
| `TestStochastic` | `%K == 100.0` when close = highest high; `%K == 0.0` when close = lowest low; `signal="overbought"` when %K > 80; `signal="oversold"` when %K < 20; `error` dict when `len < k_period` |

**Run command:** `pytest backend/agents/tools/test_technical.py -v`
