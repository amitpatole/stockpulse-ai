# VO-004: Add integration tests for data provider fallback chain

## User Story

**VO-002: Add integration tests for data provider fallback chain**

---

**User Story**

> As a backend engineer maintaining the pluggable data layer, I want a comprehensive integration test suite for `DataProviderRegistry` fallback behaviour, so that I can refactor or add providers with confidence that the fallback chain always delivers data to users even when upstream APIs fail.

---

**Acceptance Criteria**

- Primary succeeds → no fallback is called
- Primary raises → next provider is tried; its data is returned
- Primary returns `None` → next provider is tried
- Primary returns `PriceHistory` with `bars=[]` → treated as empty, falls back
- All providers raise → returns `None` cleanly (no crash)
- `is_available() = False` → provider is skipped entirely (no call made)
- Full 4-provider chain (Polygon → Finnhub → Alpha Vantage → yfinance) resolves via last resort
- `set_primary()` overrides registration order
- `create_registry()` with no keys → only yfinance registered, selected as primary
- `create_registry(finnhub_key=...)` → finnhub + yfinance registered, finnhub is primary
- `create_registry(primary='alpha_vantage')` with all keys → explicit primary wins
- Provider constructor raises in `create_registry()` → gracefully skipped, yfinance takes over
- Zero real HTTP calls — all tests use `unittest.mock`
- Runnable as `pytest backend/tests/test_data_provider_fallback.py -v`

---

**Priority: P1 — High**

The fallback chain is the core reliability guarantee of the data layer. No tests means any provider priority change silently breaks quote delivery. Real API keys aren't available in CI, so mock-based integration tests are the only safety net.

**Complexity: 2/5**

No production code changes needed. Pure test authorship against a well-defined interface. The only nuance is patching at the constructor level in `create_registry()` tests.

---

Filed as `docs/tasks/VO-002/user-story.md`. The test implementation already exists at `backend/tests/test_data_provider_fallback.py` and covers all 12 acceptance criteria above.
