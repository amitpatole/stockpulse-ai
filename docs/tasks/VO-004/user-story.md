# VO-004: Add integration tests for data provider fallback chain

## User Story

Now I have the full picture. Here's the user story:

---

## User Story: Data Provider Fallback Chain Integration Tests

**As a** backend engineer deploying Virtual Office in production,
**I want** integration tests that verify the provider fallback chain works correctly when a data source fails or returns empty data,
**so that** I can confidently refactor or swap providers without silently breaking the data layer that every chart, quote, and AI analysis depends on.

---

### Acceptance Criteria

- [ ] Test that `registry.get_quote()` skips a provider that raises an exception and returns data from the next available provider
- [ ] Test that `registry.get_quote()` skips a provider that returns `None` and continues down the chain
- [ ] Test that `registry.get_historical()` skips a provider returning empty bars (`result.bars == []`) and falls back correctly
- [ ] Test that `registry.get_quote()` returns `None` when **all** providers fail
- [ ] Test that `is_available()` returns `False` for key-required providers with no API key, and those providers are skipped without being called
- [ ] Test that `set_primary()` causes the named provider to be tried first, with fallback still functioning if it fails
- [ ] Test that `create_registry()` with no API keys registers only `yfinance` and sets it as primary
- [ ] Test that `create_registry()` with all keys registers providers in correct priority order: Polygon → Finnhub → Alpha Vantage → yfinance
- [ ] All tests use mocked providers (no real network calls); tests run in CI without API keys

---

### Priority Reasoning

**High.** The fallback chain is invisible to users but is the single most critical reliability mechanism in the data layer. A silent regression here (e.g., all providers fail but the code returns `None` instead of logging + falling back) would cascade into broken charts and AI hallucinations. We have zero test coverage on this path today.

---

### Estimated Complexity: **2 / 5**

The logic is already written and well-structured — this is purely additive test work. Mocking `DataProvider` subclasses is straightforward with `unittest.mock`. No new app code, no migrations, no API changes. A focused engineer should be able to knock this out cleanly.
