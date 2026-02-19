# VO-004: Add integration tests for data provider fallback chain

## Technical Design

## Technical Design Spec — VO-002: Data Provider Fallback Chain Integration Tests

---

### 1. Approach

Pure test authorship — **no production code changes**. The existing `DataProviderRegistry` in `backend/data_providers/` already implements the fallback chain; this task adds a mock-based integration test suite to pin that behaviour.

All external HTTP is eliminated via `unittest.mock.MagicMock`. Tests exercise the registry's public interface (`get_quote`, `get_historical`, `register`, `set_primary`) against programmatically-controlled mock providers, covering both normal operation and every failure mode.

Factory-level tests for `create_registry()` patch provider constructors at import time using `unittest.mock.patch` so no real API keys or network access are required in CI.

---

### 2. Files to Modify / Create

| Path | Action |
|---|---|
| `backend/tests/test_data_provider_fallback.py` | **Create** — sole deliverable |
| `backend/data_providers/__init__.py` | Read-only reference; no changes |
| `backend/data_providers/base.py` | Read-only reference; no changes |

No `conftest.py` additions needed — each test is self-contained.

---

### 3. Data Model Changes

None. Tests operate entirely in memory against mock objects.

---

### 4. API Changes

None. No HTTP routes are added or modified.

---

### 5. Frontend Changes

None.

---

### 6. Testing Strategy

**File:** `backend/tests/test_data_provider_fallback.py`

**Two test classes, twelve cases, zero real I/O:**

**`TestDataProviderRegistryFallback`** — exercises the live `DataProviderRegistry` with injected mocks:

| Test | Assertion |
|---|---|
| `test_primary_succeeds_no_fallback` | Secondary `.get_quote` never called |
| `test_primary_raises_falls_back` | Exception on primary → secondary result returned |
| `test_primary_returns_none_falls_back` | `None` from primary → secondary result returned |
| `test_historical_empty_bars_falls_back` | `PriceHistory(bars=[])` treated as empty, cascades |
| `test_all_fail_returns_none` | All providers raise → `None`, no crash |
| `test_unavailable_provider_skipped` | `is_available()=False` → provider's data method never called |
| `test_full_chain_last_resort` | Polygon→Finnhub→Alpha Vantage raise; yfinance returns data |
| `test_set_primary_changes_order` | `set_primary('b')` makes b first, a second |

**`TestCreateRegistry`** — patches provider constructors to test `create_registry()`:

| Test | Assertion |
|---|---|
| `test_create_registry_no_keys` | Only `YFinanceProvider` registered; it is primary |
| `test_create_registry_with_finnhub_key` | Finnhub + yfinance registered; Finnhub is primary |
| `test_create_registry_explicit_primary` | All keys + `primary='alpha_vantage'` → AV is primary |
| `test_create_registry_provider_init_failure` | Constructor raises → provider skipped; yfinance takes over |

**Helper utilities** (module-level, not test methods):
- `make_provider(name, available, quote_result, history_result)` — returns a `MagicMock` satisfying the `DataProvider` interface
- `sample_quote() / sample_history()` — canonical fixture data

**Run command:**
```
pytest backend/tests/test_data_provider_fallback.py -v
```
