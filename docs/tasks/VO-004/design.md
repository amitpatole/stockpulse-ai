# VO-004: Add integration tests for data provider fallback chain

## Technical Design

Now I have a clear picture. The test file already exists with strong coverage. Let me identify the gap against the acceptance criteria before writing the spec.

The existing `test_create_registry_explicit_primary` tests all-keys registration but forces `primary='alpha_vantage'` — it never validates auto-selection picks Polygon first. And `test_set_primary_changes_order` only proves the new primary succeeds, not that fallback still triggers when the new primary fails. Those are the two missing cases.

---

## Technical Design Spec: Data Provider Fallback Chain Integration Tests

### Approach

The test infrastructure is already in place (`backend/tests/test_data_provider_fallback.py`, 381 lines). All required helpers (`make_provider`, `_build_registry`, `_mock_provider_class`) exist. The work is purely **additive**: fill two coverage gaps in `TestDataProviderRegistryFallback` and `TestCreateRegistry`, then run the suite to confirm all 12 acceptance criteria pass.

No new app code. No mocking framework changes. No fixtures to add.

---

### Files to Modify/Create

| File | Action |
|---|---|
| `backend/tests/test_data_provider_fallback.py` | Add 2 test methods (described below) |

---

### Data Model Changes

None.

### API Changes

None.

### Frontend Changes

None.

---

### Testing Strategy

**Gap 1 — AC #6:** `set_primary()` fallback when explicit primary fails

Add `test_set_primary_fails_then_falls_back` inside `TestDataProviderRegistryFallback`:
- Register `polygon`, `finnhub`, `yfinance` in that order
- Call `registry.set_primary('yfinance')` — yfinance becomes primary
- Configure yfinance to raise `Exception('unavailable')`
- Assert `get_quote()` falls back and returns data from `polygon` or `finnhub`
- Assert `yfinance.get_quote` was called, and at least one fallback was called

**Gap 2 — AC #8:** `create_registry()` with all keys auto-selects Polygon as primary

Add `test_create_registry_all_keys_polygon_is_primary` inside `TestCreateRegistry`:
- Mock all four provider classes via `_mock_provider_class`
- Call `create_registry(polygon_key='pk', finnhub_key='fk', alpha_vantage_key='ak')` — no explicit `primary`
- Assert all four providers are registered
- Assert `registry.get_primary().get_provider_info().name == 'polygon'`

**Existing coverage confirmed against remaining ACs:**

| AC | Covered by |
|---|---|
| Exception skips to next | `test_primary_raises_falls_back` |
| None skips to next | `test_primary_returns_none_falls_back` |
| Empty bars fallback | `test_historical_empty_bars_falls_back` |
| All fail → None | `test_all_fail_returns_none` |
| `is_available=False` skipped | `test_unavailable_provider_skipped` |
| No keys → yfinance only | `test_create_registry_no_keys` |
| Constructor failure graceful | `test_create_registry_provider_init_failure` |

**CI compatibility:** All tests use `unittest.mock`. No network calls. No API keys needed. Run with:
```
python -m pytest backend/tests/test_data_provider_fallback.py -v
```

---

**Total delta: ~25 lines across 2 new test methods.** Everything else is already written and correct.
