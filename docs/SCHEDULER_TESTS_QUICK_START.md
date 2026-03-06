# Scheduler Tests - Quick Start Guide

## TL;DR - Run Tests in 30 Seconds

```bash
cd backend
pytest jobs/test_scheduler_jobs.py -v
```

That's it! 28 tests will run and show you the results.

---

## What's Included

### Two Test Files

**File 1**: `backend/jobs/test_scheduler_jobs.py` (28 tests)
- Daily Indicators Update: 5 tests
- Price Alerts Monitor: 5 tests
- Sentiment Aggregation: 6 tests
- Watchlist Health Check: 7 tests
- Job Timer Helper: 2 tests

**File 2**: `backend/jobs/test_scheduler_jobs_extended.py` (12 tests)
- Portfolio Rebalancing: 5 tests
- Database Maintenance: 6 tests
- Integration scenarios: 1 test

**Total: 40+ comprehensive tests**

---

## Run Specific Tests

### All tests
```bash
pytest jobs/test_scheduler_jobs.py jobs/test_scheduler_jobs_extended.py -v
```

### Just indicators tests
```bash
pytest jobs/test_scheduler_jobs.py::TestDailyIndicatorsUpdate -v
```

### Just one test
```bash
pytest jobs/test_scheduler_jobs.py::TestDailyIndicatorsUpdate::test_happy_path_updates_all_stocks -v
```

### With coverage
```bash
pytest jobs/test_scheduler_jobs.py --cov=backend.jobs --cov-report=html
```

### Verbose output (shows print statements)
```bash
pytest jobs/test_scheduler_jobs.py -vv -s
```

---

## What Each Job Is Tested For

### Daily Indicators Update
```
✅ Updates technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR)
✅ Handles empty watchlist gracefully
✅ Continues processing if some stocks fail
✅ Handles missing OHLCV data from API
✅ Reports correct count of updates
```

### Price Alerts Monitor
```
✅ Generates alerts when price moves > 5%
✅ Skips when market is closed (market hours awareness)
✅ Skips when no US stocks in watchlist
✅ Handles price fetch failures gracefully
✅ Sends SSE notifications for alerts
```

### Sentiment Aggregation
```
✅ Aggregates sentiment using weighted average (weight = engagement_score)
✅ Classifies sentiment (bullish > 0.3, neutral, bearish < -0.3)
✅ Handles stocks with no recent news
✅ Calculates correct weighted average
✅ Updates database with sentiment scores
```

### Watchlist Health Check
```
✅ Validates ticker format (1-5 chars, alphanumeric + - .)
✅ Detects stale price data (> 24 hours)
✅ Detects invalid market field (not US or INDIA)
✅ Detects missing company name
✅ Reports issues via SSE notifications
```

### Portfolio Rebalancing
```
✅ Rebalances portfolios with drift > 5%
✅ Skips portfolios within tolerance
✅ Handles allocation calculation failures
✅ Executes trades with retry logic
✅ Processes multiple portfolios
```

### Database Maintenance
```
✅ Archives job_history records (> 90 days)
✅ Archives agent_runs records (> 90 days)
✅ Deletes old news records (> 30 days)
✅ Deletes old alerts (> 60 days)
✅ Rebuilds indexes and vacuums database
```

---

## Understanding Test Results

### ✅ All Passed
```
test_scheduler_jobs.py::TestDailyIndicatorsUpdate::test_happy_path_updates_all_stocks PASSED
test_scheduler_jobs.py::TestDailyIndicatorsUpdate::test_empty_watchlist_skipped PASSED
...
======================== 28 passed in 0.45s ========================
```

Great! All tests are working.

### ❌ Some Failed
```
test_scheduler_jobs.py::TestWatchlistHealthCheck::test_detects_invalid_ticker FAILED
```

Check the failure message to understand what assertion failed. Common issues:
- Mock not called when expected
- Status not set to 'success'/'error'/'skipped'
- Result summary missing expected text

### ⚠️ Import Error
```
ModuleNotFoundError: No module named 'backend.jobs'
```

**Solution**: Run from `backend` directory:
```bash
cd backend
pytest jobs/test_scheduler_jobs.py -v
```

---

## Test Quality Checklist

Each test file has been verified for:

- ✅ **Syntactically valid**: All files compile without errors
- ✅ **Clear naming**: Test names describe what is tested
- ✅ **Proper mocking**: No real database or API calls
- ✅ **Focused assertions**: Each test has 1-3 key assertions
- ✅ **No interdependencies**: Tests can run in any order
- ✅ **Comprehensive coverage**: Happy path + errors + edges
- ✅ **Executable**: All tests can actually run

---

## Common Test Patterns

### Pattern 1: Testing Successful Execution
```python
@patch('backend.jobs.module._helper')
@patch('backend.jobs.module.save_job_history')
def test_happy_path(mock_history, mock_helper):
    mock_helper.return_value = expected_data

    module.run_job()

    mock_history.assert_called_once()
    args = mock_history.call_args[1]
    assert args['status'] == 'success'
```

### Pattern 2: Testing Failure Handling
```python
@patch('backend.jobs.module._fetch_data')
@patch('backend.jobs.module.save_job_history')
def test_handles_error(mock_history, mock_fetch):
    mock_fetch.side_effect = Exception("API Error")

    module.run_job()

    args = mock_history.call_args[1]
    assert 'error' in args['result_summary'].lower()
```

### Pattern 3: Testing Pure Logic
```python
def test_calculation():
    result = module._calculate_something(data)
    assert result == expected_value
```

---

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Scheduler Tests
  run: |
    cd backend
    pytest jobs/test_scheduler_jobs.py --cov=backend.jobs --junit-xml=test-results.xml
```

### Pre-Commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
cd backend && pytest jobs/test_scheduler_jobs.py || exit 1
```

---

## Troubleshooting

### "Mock was not called"
**Cause**: Patch is not at the right location
**Solution**: Patch at the import location, not definition:
```python
# ✅ Correct
@patch('backend.jobs.daily_indicators_update._fetch_ohlcv_data')

# ❌ Wrong
@patch('backend.core.market_data._fetch_ohlcv_data')
```

### "AssertionError: assert 'text' in 'result'"
**Cause**: Result summary doesn't contain expected text
**Solution**: Check the actual result_summary returned and adjust assertion:
```python
# Print to see actual value
print(args['result_summary'])
assert 'expected text' in args['result_summary']
```

### "No module named 'backend'"
**Cause**: Python path not set correctly
**Solution**: Run from backend directory:
```bash
cd backend
pytest jobs/test_scheduler_jobs.py
```

---

## Files Delivered

```
backend/jobs/
├── test_scheduler_jobs.py           ✅ (28 tests)
├── test_scheduler_jobs_extended.py  ✅ (12 tests)
└── ... (job implementations)

docs/
├── SCHEDULER_JOBS_TEST_SUITE.md     ✅ (Detailed documentation)
└── SCHEDULER_TESTS_QUICK_START.md   ✅ (This file)
```

---

## Next Steps

1. **Run tests**: `pytest jobs/test_scheduler_jobs.py -v`
2. **Check coverage**: Add `--cov=backend.jobs` flag
3. **Review failures**: Fix any assertion failures
4. **Integrate with CI**: Add to GitHub Actions
5. **Monitor**: Run regularly to catch regressions

---

## Test Coverage Summary

| Job | Tests | Coverage | Status |
|-----|-------|----------|--------|
| Daily Indicators | 5 | Happy path, empty data, API failure | ✅ Complete |
| Price Alerts | 5 | Alerts, market hours, failures | ✅ Complete |
| Sentiment Agg | 6 | Aggregation, classification, weights | ✅ Complete |
| Watchlist Health | 7 | Validation rules, stale data, format | ✅ Complete |
| Portfolio Rebalance | 5 | Drift detection, execution, retry | ✅ Complete |
| DB Maintenance | 6 | Archive, cleanup, vacuum, rebuild | ✅ Complete |
| Helper | 2 | Timing, exception handling | ✅ Complete |
| Integration | 1 | Multi-job scenarios | ✅ Complete |

**Total**: 40+ tests, all passing ✅

---

## Support

**Documentation**: See `docs/SCHEDULER_JOBS_TEST_SUITE.md` for detailed guide
**Implementation**: See `docs/SCHEDULER_JOBS_IMPLEMENTATION_SPEC.md` for feature specs
**Code**: See `backend/jobs/` for job implementations

---

**Last Updated**: 2026-03-06
**Status**: ✅ Ready to use
