# VO-002: Add integration tests for data provider fallback chain

## User Story

**As a** backend engineer maintaining the pluggable data layer,
**I want** a comprehensive integration test suite for `DataProviderRegistry` fallback behaviour,
**so that** I can refactor or add providers with confidence that the fallback chain always delivers data to users even when upstream APIs fail.

---

## Acceptance Criteria

- [ ] Test: primary provider succeeds → no fallback provider is called
- [ ] Test: primary raises an exception → next provider in chain is called and its data is returned
- [ ] Test: primary returns `None` → next provider in chain is called
- [ ] Test: primary returns `PriceHistory` with `bars=[]` → treated as empty and falls back
- [ ] Test: all providers raise → `get_quote` / `get_historical` return `None` (no crash)
- [ ] Test: provider with `is_available() = False` is skipped entirely (no call made)
- [ ] Test: full four-provider chain (Polygon → Finnhub → Alpha Vantage → yfinance) resolves via last resort
- [ ] Test: `set_primary()` overrides registration order for quote resolution
- [ ] Test: `create_registry()` with no API keys registers only yfinance and selects it as primary
- [ ] Test: `create_registry(finnhub_key=...)` registers finnhub + yfinance; finnhub becomes primary
- [ ] Test: `create_registry(primary='alpha_vantage')` with all keys overrides auto-selection
- [ ] Test: provider constructor raises during `create_registry()` → provider is skipped gracefully; yfinance remains primary
- [ ] All tests use `unittest.mock` — zero real HTTP calls
- [ ] Test file runnable standalone: `pytest backend/tests/test_data_provider_fallback.py -v`

---

## Priority Reasoning

**P1 — High.** The fallback chain is the core reliability guarantee of the data layer. Without tests, any change to `DataProviderRegistry` or `create_registry()` (adding a new provider, changing priority order, handling a new error type) risks silently breaking the chain. Users would see missing quotes or empty charts with no obvious cause. Given that real API keys are environment-dependent and unavailable in CI, mock-based integration tests are the only practical safety net.

---

## Complexity: 2 / 5

The registry logic is already written and the `DataProvider` interface is well-defined. The work is entirely in test setup: building mock providers, wiring them into a registry, and asserting call sequences. No production code changes required. The main subtlety is correctly testing the `create_registry()` factory via constructor-level mocks rather than instance-level mocks.
