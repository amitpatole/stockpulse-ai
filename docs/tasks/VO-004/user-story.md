# VO-004: Add integration tests for data provider fallback chain

## User Story

Here's the user story based on the actual fallback logic in `base.py:148-186`:

---

## User Story: Integration Tests for Data Provider Fallback Chain

**As a** backend engineer,
**I want** integration tests that verify `DataProviderRegistry` correctly falls back through Polygon → Finnhub → Alpha Vantage → yfinance when a provider fails or returns empty data,
**so that** I can confidently modify or extend the provider system without silently breaking the reliability guarantee users depend on for uninterrupted quote and history data.

---

### Acceptance Criteria

**Fallback on exception (`get_quote` and `get_historical`)**
- When the primary provider raises an exception, the registry tries the next provider in `_fallback_order` and returns its result
- When all providers except yfinance raise exceptions, yfinance result is returned
- When all providers raise exceptions, `None` is returned (no crash)

**Fallback on empty/None result**
- When a provider returns `None` for `get_quote`, the next provider is tried
- When a provider returns a `PriceHistory` with empty `bars`, the next provider is tried (see `base.py:181`)
- A provider returning a valid non-empty result stops the chain — subsequent providers are NOT called

**Provider availability gating**
- A provider with `is_available() == False` (no API key) is skipped entirely, not tried-then-fallen-back-from
- yfinance (no key required) is always the last resort

**Primary provider override**
- When `set_primary()` is called, that provider is tried first before `_fallback_order` sequence

**Test infrastructure**
- All tests use `unittest.mock` — no real API calls
- Tests live in `backend/tests/test_data_provider_fallback.py`
- Tests run with `pytest` and pass in CI with no environment variables set

---

### Priority Reasoning

**Medium-High.** The fallback chain is the core reliability guarantee of the data layer — every quote and chart in the UI depends on it. Currently there are zero tests for this logic. The `get_historical` empty-bars check (`base.py:181`) is a subtle edge case that's easy to break silently. Adding providers or changing priority order should be validated by a test, not manual QA.

---

### Estimated Complexity: **2 / 5**

Pure test authorship — no production code changes. The existing `DataProviderRegistry` and `DataProvider` ABC are well-structured for mocking. The main work is setting up a handful of mock providers and asserting call order. No external dependencies or database fixtures needed.
