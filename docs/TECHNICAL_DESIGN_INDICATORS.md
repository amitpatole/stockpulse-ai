# Technical Design: Missing Technical Indicators (SMA, EMA, MACD, Bollinger Bands, Stochastic, ATR, ADX)

**Ticket**: Task to implement 9 missing indicators
**Current Gap**: Only RSI is fully implemented; 90% gap vs. 10 promised indicators
**Target Indicators**: SMA, EMA, MACD, Bollinger Bands, Stochastic, ATR, ADX (+RSI consolidation)
**Effort**: ~16-20 story points (2 sprints)

---

## 1. APPROACH

### Strategy: Modular Indicator Library
Extract indicators from monolithic `ai_analytics.py` → new `indicators.py` module with:
- **Single Responsibility**: Each indicator = pure function operating on OHLCV arrays
- **Composability**: Higher-order indicators (MACD, Bollinger Bands) use base indicators (EMA, SMA)
- **Robustness**: Handle edge cases (insufficient data, zero/null values, divide-by-zero)
- **Testability**: 100% unit test coverage with deterministic test data

### Implementation Pattern
```python
# backend/core/indicators.py
class TechnicalIndicators:
    @staticmethod
    def sma(prices: List[float], period: int = 20) -> float
    @staticmethod
    def ema(prices: List[float], period: int = 20) -> float
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict
    @staticmethod
    def stochastic(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Dict
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float
    @staticmethod
    def adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Dict
    @staticmethod
    def macd(prices: List[float]) -> Dict  # Move from ai_analytics.py
```

---

## 2. FILES TO MODIFY/CREATE

| File | Action | Reason |
|------|--------|--------|
| `backend/core/indicators.py` | **CREATE** | New modular indicator library (180-220 lines) |
| `backend/core/ai_analytics.py` | MODIFY | Import `TechnicalIndicators` class; refactor `calculate_ai_rating()` to use new module |
| `backend/tests/test_indicators.py` | **CREATE** | 40-50 unit tests covering all 7 indicators (420-500 lines) |
| `backend/api/analysis.py` | OPTIONAL | Add `/api/indicators/<ticker>` endpoint if UI needs raw indicator values |

---

## 3. DATA MODEL CHANGES

**NO schema changes required.** Indicators are computed on-the-fly from OHLCV price data.

Existing table usage:
- `stock_prices` (timestamp, ticker, open, high, low, close, volume) - read-only
- `ai_ratings` (ticker, rating_date, technical_score, sentiment_score, combined_score) - already stores composite scores

**Future optimization** (Post-MVP): Add `indicator_cache` table for expensive calculations (ATR, ADX with backfill).

---

## 4. API CHANGES

### Existing endpoint (unchanged behavior):
```
GET /api/ratings/<ticker>
```
Response now includes **breakdown of individual indicators**:
```json
{
  "ticker": "AAPL",
  "rating": "BUY",
  "technical_score": 72.5,
  "breakdown": {
    "rsi": 65.0,
    "sma_20": { "value": 180.50, "signal": "bullish" },
    "ema_12": 181.20,
    "macd": { "value": 0.75, "signal": 0.50, "histogram": 0.25, "trend": "bullish" },
    "bollinger_bands": { "upper": 185.0, "middle": 180.0, "lower": 175.0, "position": 0.6 },
    "stochastic": { "k": 72.0, "d": 68.0, "signal": "overbought" },
    "atr": 2.15,
    "adx": { "value": 42.5, "trend_strength": "strong" }
  },
  "updated_at": "2026-03-03T14:22:00Z"
}
```

### Optional new endpoint (if UI requests):
```
GET /api/indicators/<ticker>?period=1mo
Response: { rsi, sma, ema, macd, bollinger_bands, stochastic, atr, adx, time_series }
```

---

## 5. FRONTEND CHANGES

**No breaking changes.** Existing rating display stays unchanged.

### Optional UI enhancements (separate feature):
- **Indicator Details Panel**: Expandable section on analysis page showing breakdown
- **Technical Scorecard**: Visual display of each indicator (gauge/sparkline)
- **Multi-indicator Chart**: Overlay MACD, Bollinger Bands on price chart (requires recharts/lightweight-charts update)

Currently, frontend consumes only `rating` field. Breakdown data is ignored but available for future use.

---

## 6. TESTING STRATEGY

### Unit Tests (40-50 tests, `backend/tests/test_indicators.py`)

**For each indicator**: Happy path + edge cases
```python
class TestSimpleIndicators:
    def test_sma_basic_calculation()  # Known dataset, known output
    def test_sma_insufficient_data()  # <period points → fallback
    def test_sma_zero_prices()        # All zeros
    def test_sma_null_handling()      # None values filtered

class TestComplexIndicators:
    def test_macd_trend_detection()   # Bullish/bearish/neutral
    def test_bollinger_position()     # Price relative to bands (0-1)
    def test_stochastic_overbought()  # K/D signals
    def test_atr_volatility()         # ATR responds to price moves
    def test_adx_trend_strength()     # ADX increases in strong trends

class TestEdgeCases:
    def test_insufficient_data_all()        # All indicators with <period data
    def test_flat_prices()                  # No movement (ATR=0, RSI=50)
    def test_gap_moves()                    # Large jumps (ATR spikes)
    def test_extreme_volatility()           # 100%+ single-day moves
```

### Integration Tests (existing structure)
- `test_ai_analytics.py`: Verify `calculate_ai_rating()` uses new indicators
- `test_api_analysis.py`: Verify endpoint returns indicator breakdown

### Quality Acceptance Criteria
- ✅ All 7 indicators implemented and callable
- ✅ 40+ passing unit tests (target 80%+ code coverage on `indicators.py`)
- ✅ Edge cases handled (insufficient data, null, zero, extreme values)
- ✅ Type hints complete (no `Any`)
- ✅ Calculation accuracy verified against known reference values (Yahoo Finance, TA-Lib)
- ✅ Zero external dependencies (no `ta-lib` or `pandas`, use stdlib + numpy if approved)

---

## 7. DEPENDENCY & SEQUENCING

### Critical Path
1. ✅ Write `indicators.py` module (core logic)
2. ✅ Write comprehensive unit tests
3. ✅ Integrate with `ai_analytics.py` (refactor `calculate_ai_rating()`)
4. ✅ Regression test: `test_ai_ratings.py` still passes
5. 🔵 Optional: Add API endpoint + frontend UI

### Blocks
- Do NOT ship new API endpoint until indicators are tested + stable
- Do NOT modify `ai_ratings` schema until caching decision finalized

---

## 8. TECHNICAL NOTES

### Numeric Stability
- Use `float` for all calculations (sufficient precision for price/indicator values)
- Clamp indicator results (RSI: 0-100, stochastic K/D: 0-100, ADX: 0-100)
- Handle divide-by-zero gracefully (return 50 for RSI if avg_loss=0, etc.)

### Performance
- All indicators O(n) linear time in data length
- For 1000 daily candles (5 years): <10ms per ticker
- No database hits from indicator calculations

### References (for accuracy validation)
- **SMA/EMA**: Stock market standard formulas
- **MACD**: 12-26-9 EMA configuration (industry standard)
- **Bollinger Bands**: 20-period SMA ± 2 std. deviations
- **Stochastic**: 14-period K, 3-period D smoothing
- **ATR**: 14-period true range average
- **ADX**: 14-period directional movement index

---

## Summary

| Aspect | Detail |
|--------|--------|
| **Lines of Code** | ~200 (indicators.py) + ~450 (tests) |
| **Effort** | 16-20 story points |
| **Timeline** | 2 sprints (1 sprint core + 1 sprint tests + integration) |
| **Risk** | LOW - isolated module, no schema changes, backward compatible |
| **Testing** | 100% unit test coverage required before merge |
| **Doc Updates** | Add indicator definitions to API docs; update BACKEND_AUDIT.md |
