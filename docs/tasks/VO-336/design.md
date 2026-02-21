# VO-336: Timezone Display Bug — Technical Design Spec

## Approach

Mechanical, grep-driven sweep across all backend Python files. Replace every naive datetime construction with a tz-aware UTC equivalent. The fix is confined to three patterns:

1. `datetime.fromtimestamp(ts)` → `datetime.fromtimestamp(ts, tz=timezone.utc)`
2. `datetime.utcnow()` → `datetime.now(timezone.utc)`
3. `datetime.strptime(...)` / `datetime.now()` used as timestamps → add `.replace(tzinfo=timezone.utc)` or swap to `datetime.now(timezone.utc)`

No schema changes. No new dependencies. The standard library `timezone.utc` sentinel (already in `datetime`) is all that's needed. JSON serialisation in `stock_data.py:148` already calls `.isoformat()`; once `Quote.timestamp` is tz-aware it will automatically emit `+00:00`.

---

## Files to Modify

### Core fix — data providers (source of the bug)

| File | Naive calls to fix |
|---|---|
| `backend/data_providers/finnhub_provider.py` | `fromtimestamp(ts)` → `fromtimestamp(ts, tz=timezone.utc)` (line 135); `datetime.now()` → `datetime.now(timezone.utc)` (line 97) |
| `backend/data_providers/polygon_provider.py` | `fromtimestamp(latest.timestamp / 1000)` (155); `fromtimestamp(trade['t'] / 1e9)` (178); `datetime.now()` fallback (179); `fromtimestamp(bar['t'] / 1000)` (198); `datetime.now()` date-range calls (114, 139, 140, 185, 186, 209, 210) |
| `backend/data_providers/yfinance_provider.py` | `fromtimestamp(timestamps[idx])` (194); `datetime.now()` fallback (194, 237); `datetime.now()` tracking (106) |
| `backend/data_providers/alpha_vantage_provider.py` | `datetime.now()` quote ts fallback (157); `datetime.strptime(latest_day, '%Y-%m-%d')` → add `.replace(tzinfo=timezone.utc)` (160); `datetime.now().timestamp()` cutoff (218); `datetime.strptime(date_str, ...)` bar parsing (224, 226) → `.replace(tzinfo=timezone.utc)`; `datetime.now()` tracking (109) |
| `backend/data_providers/custom_provider.py` | Fix the template comment example (line 108) so new custom providers don't copy the bug |

### Secondary — agent + job infrastructure (`utcnow()` → `datetime.now(timezone.utc)`)

| File | Lines |
|---|---|
| `backend/agents/base.py` | 100, 105, 120 |
| `backend/app.py` | 150 |
| `backend/scheduler.py` | 215 |
| `backend/jobs/_helpers.py` | 71, 152 |
| `backend/jobs/daily_summary.py` | 110, 134 |
| `backend/jobs/morning_briefing.py` | 90 |
| `backend/jobs/regime_check.py` | 72 |
| `backend/jobs/technical_monitor.py` | 84 |
| `backend/jobs/weekly_review.py` | 112, 137 |

### Tests

| File | Change |
|---|---|
| `backend/tests/test_data_provider_fallback.py` | Update `sample_quote()` (line 41): `datetime(2024, 1, 15, 10, 0)` → `datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)`; add `assert result.timestamp.tzinfo is not None` to quote-returning tests |

---

## Data Model Changes

None. `Quote.timestamp` is typed `datetime` in `base.py:19`; it already accepts tz-aware values. No DB schema or migration needed.

---

## API Changes

None. `quote.timestamp.isoformat()` in `stock_data.py:148` emits `2024-01-15T10:00:00+00:00` once the object is tz-aware — still valid JSON, same field name, strictly more informative. Response contract is unchanged.

---

## Frontend Changes

None. JavaScript's `new Date("2024-01-15T10:00:00+00:00")` already parses ISO8601 with offset correctly, and was silently treating the previous naive string as local time — which was the bug. The fix is transparent to frontend code.

---

## Testing Strategy

**Existing regression**: Run `pytest backend/tests/test_data_provider_fallback.py -v` — all tests must pass after updating `sample_quote()` to use tz-aware datetime.

**New assertions** (add inline to existing `TestDataProviderRegistryFallback` tests):
```python
assert result.timestamp.tzinfo is not None          # tz-aware
assert result.timestamp.tzinfo == timezone.utc      # specifically UTC
```

**UTC consistency test** (new `test_same_unix_ts_all_providers`): Feed the same Unix timestamp (e.g. `1705276800`) through a mock of each concrete provider's quote-building code; assert all four return the identical `datetime` object.

**isoformat output test**: Assert `quote.timestamp.isoformat()` ends with `+00:00` (never a bare `T...` without offset).

**Grep verification** (CI gate): Add a `grep -rn "datetime\.utcnow\|fromtimestamp([^,)]*)" backend/` step that fails if any matches remain outside comments and test fixtures.
