# VO-004: Add integration tests for data provider fallback chain

## Technical Design

## Technical Design Spec: Data Provider Fallback Integration Tests

### Approach

Write a self-contained pytest test module that exercises `DataProviderRegistry` (from `base.py`) and `create_registry()` (from `__init__.py`) using `unittest.mock`. No real HTTP calls. Providers are replaced with `MagicMock` instances configured to raise, return `None`, or return valid data objects, allowing precise control over each fallback scenario.

The registry's fallback logic lives in `DataProviderRegistry.get_quote()` (lines 148-166) and `get_historical()` (168-186) in `base.py` — both iterate `_fallback_order`, skip unavailable providers, catch exceptions, and skip `None`/empty results. Tests must cover all three failure modes.

---

### Files to Modify/Create

| Action | Path |
|--------|------|
| **Create** | `backend/tests/test_data_provider_fallback.py` |

No other files need changes.

---

### Data Model Changes

None.

---

### API Changes

None.

---

### Frontend Changes

None.

---

### Testing Strategy

**File:** `backend/tests/test_data_provider_fallback.py`

**Fixtures:**
- `make_provider(name, available, quote_result, history_result)` — helper that returns a `MagicMock` conforming to `DataProvider` interface, with `is_available()` and `get_provider_info()` pre-configured.
- `sample_quote(source)` / `sample_history(source)` — factory helpers returning valid `Quote` / `PriceHistory` dataclass instances.

**Test cases for `DataProviderRegistry`:**

| Test | Scenario |
|------|----------|
| `test_primary_succeeds_no_fallback` | Primary returns valid data; assert second provider never called |
| `test_primary_raises_falls_back` | Primary raises `Exception`; fallback returns data |
| `test_primary_returns_none_falls_back` | Primary returns `None`; fallback returns data |
| `test_historical_empty_bars_falls_back` | Primary returns `PriceHistory` with `bars=[]`; fallback returns non-empty |
| `test_all_fail_returns_none` | All providers raise; `get_quote()` returns `None` |
| `test_unavailable_provider_skipped` | Provider with `is_available()=False` never called |
| `test_full_chain_last_resort` | Three providers raise/return None; fourth (yfinance-like) succeeds |
| `test_set_primary_changes_order` | `set_primary('third')` causes third provider to be tried first |

**Test cases for `create_registry()`:**

| Test | Scenario |
|------|----------|
| `test_create_registry_no_keys` | No API keys → only yfinance registered, primary is yfinance |
| `test_create_registry_with_finnhub_key` | `finnhub_key='x'` → finnhub registered and set as primary |
| `test_create_registry_explicit_primary` | Keys for all three → `primary='alpha_vantage'` overrides auto-select |
| `test_create_registry_provider_init_failure` | Provider constructor raises → gracefully skipped, next provider becomes primary |

**Execution:**
```
python -m pytest backend/tests/test_data_provider_fallback.py -v
```

No new dependencies required — all mocking via stdlib `unittest.mock`.
