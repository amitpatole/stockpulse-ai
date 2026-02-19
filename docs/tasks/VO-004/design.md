# VO-004: Add integration tests for data provider fallback chain

## Technical Design

## Technical Design Spec: Integration Tests for Data Provider Fallback Chain

**Status note:** `backend/tests/test_data_provider_fallback.py` already exists and is fully implemented (426 lines). This spec documents what's there and what remains.

---

### 1. Approach

Pure test authorship — no production code changes. Tests directly instantiate `DataProviderRegistry`, register `MagicMock` providers via `make_provider()`, then assert call order and return values. `create_registry()` tests use `unittest.mock.patch` to intercept provider class constructors, keeping all tests hermetic.

The fallback chain under test (`base.py:148–186`) iterates `_fallback_order`, skipping unavailable providers (`is_available() == False`) and falling through on both exceptions and falsy results. For `get_historical`, the additional guard at line 181 (`result and result.bars`) makes empty-bars a distinct failure mode requiring its own test case.

---

### 2. Files to Modify/Create

| Action | Path |
|--------|------|
| **Already created** | `backend/tests/test_data_provider_fallback.py` |
| No changes needed | `backend/data_providers/base.py` |
| No changes needed | `backend/data_providers/__init__.py` |

No `conftest.py` or `pytest.ini` required — tests are self-contained.

---

### 3. Data Model Changes

None. Tests use in-memory `DataProvider` mocks and the existing `Quote`, `PriceBar`, `PriceHistory` dataclasses.

---

### 4. API Changes

None.

---

### 5. Frontend Changes

None.

---

### 6. Testing Strategy

**`TestDataProviderRegistryFallback`** (8 cases) — tests the registry directly:

| Test | Verifies |
|------|----------|
| `test_primary_succeeds_no_fallback` | Chain stops at first success |
| `test_primary_raises_falls_back` | Exception triggers next provider |
| `test_primary_returns_none_falls_back` | `None` result triggers fallback |
| `test_historical_empty_bars_falls_back` | `bars=[]` triggers fallback (`base.py:181`) |
| `test_all_fail_returns_none` | Exhausted chain returns `None`, no crash |
| `test_unavailable_provider_skipped` | `is_available()==False` → no `get_quote` call |
| `test_full_chain_last_resort` | Full 4-provider chain, last-resort wins |
| `test_set_primary_changes_order` | `set_primary()` puts provider first |
| `test_set_primary_fails_then_falls_back` | Overridden primary fails, fallback resumes |

**`TestCreateRegistry`** (5 cases) — tests the factory function with patched constructors:

| Test | Verifies |
|------|----------|
| `test_create_registry_no_keys` | Only yfinance registered, premium ctors not called |
| `test_create_registry_with_finnhub_key` | Finnhub registered with correct key, becomes primary |
| `test_create_registry_explicit_primary` | `primary=` kwarg overrides auto-selection |
| `test_create_registry_all_keys_polygon_is_primary` | Polygon wins auto-selection (highest priority) |
| `test_create_registry_provider_init_failure` | Constructor `RuntimeError` → provider skipped, yfinance fallback |

**Run command:**
```
python -m pytest backend/tests/test_data_provider_fallback.py -v
```

No environment variables required; all tests pass with zero real API calls.
