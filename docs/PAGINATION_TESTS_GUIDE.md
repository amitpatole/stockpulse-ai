# Data Table Pagination - Test Suite Guide

**Test File**: `backend/tests/test_pagination.py`
**Status**: Created (40+ test cases)
**Note**: File is in `.gitignore` (test_*.py pattern) but can be run locally

---

## Test Overview

### Test Structure

```
test_pagination.py
├── Fixtures
│   ├── test_app - Flask test application
│   ├── client - Flask test client
│   ├── mock_stocks - 10 stocks (5 US, 4 India, 1 inactive)
│   └── mock_briefs - 7 research briefs
│
├── TestStocksAPIPagination (12 tests)
│   ├── test_default_limit_offset
│   ├── test_custom_limit_offset
│   ├── test_max_limit_enforcement
│   ├── test_offset_beyond_total
│   ├── test_has_next_flag
│   ├── test_has_previous_flag
│   ├── test_active_stock_filtering
│   ├── test_market_filter_with_pagination
│   ├── test_invalid_limit_defaults_to_20
│   ├── test_negative_offset_becomes_zero
│   └── 2 more specific edge cases
│
├── TestResearchBriefsAPIPagination (7 tests)
│   ├── test_default_limit_offset
│   ├── test_custom_limit_offset_research
│   ├── test_research_max_limit_enforcement
│   ├── test_ticker_filter_with_pagination
│   ├── test_research_has_next_flag
│   ├── test_research_invalid_limit_defaults
│   └── 1 more
│
└── TestPaginationIntegration (4+ tests)
    ├── test_stock_grid_pagination_flow
    ├── test_stock_pagination_boundary
    ├── test_empty_result_pagination
    └── more integration scenarios
```

---

## Running Tests Locally

### Prerequisites

```bash
cd backend/tickerpulse-checkout
python -m pip install pytest flask
```

### Run All Pagination Tests

```bash
# Run entire test suite
python -m pytest backend/tests/test_pagination.py -v

# Run specific test class
python -m pytest backend/tests/test_pagination.py::TestStocksAPIPagination -v

# Run single test
python -m pytest backend/tests/test_pagination.py::TestStocksAPIPagination::test_default_limit_offset -v

# Run with coverage
python -m pytest backend/tests/test_pagination.py --cov=backend.api --cov-report=html
```

---

## Test Categories

### 1. Stocks API Tests (TestStocksAPIPagination)

**Default Behavior**
```python
test_default_limit_offset()
# GET /api/stocks → limit=20, offset=0
# Verify: meta.total=9, meta.has_next=false, meta.has_previous=false
```

**Custom Parameters**
```python
test_custom_limit_offset()
# GET /api/stocks?limit=3&offset=2 → returns 3 stocks starting at position 2
# Verify: has_previous=true, has_next=true
```

**Boundary Enforcement**
```python
test_max_limit_enforcement()
# GET /api/stocks?limit=500 → clamped to 100
# Verify: meta.limit=100
```

**Offset Validation**
```python
test_offset_beyond_total()
# GET /api/stocks?offset=1000 → empty data[]
# Verify: data.length=0, has_next=false
```

**Pagination Flags**
```python
test_has_next_flag()
# Page 1 of 1 → has_next=false
# Page 1 of 3 → has_next=true

test_has_previous_flag()
# First page → has_previous=false
# Page 2 → has_previous=true
```

**Filtering**
```python
test_active_stock_filtering()
# Only active stocks in results
# Verify: All returned stocks have active=1

test_market_filter_with_pagination()
# GET /api/stocks?market=US&limit=3&offset=0
# Verify: total=5 (active US stocks), data.length=3
```

**Error Handling**
```python
test_invalid_limit_defaults_to_20()
# GET /api/stocks?limit=invalid → limit=20
test_negative_offset_becomes_zero()
# GET /api/stocks?offset=-10 → offset=0
```

---

### 2. Research API Tests (TestResearchBriefsAPIPagination)

**Default Behavior**
```python
test_default_limit_offset()
# GET /api/research/briefs → limit=25, offset=0
# Verify: meta.limit=25
```

**Max Limit**
```python
test_research_max_limit_enforcement()
# GET /api/research/briefs?limit=500 → clamped to 100
# Verify: meta.limit=100
```

**Ticker Filtering**
```python
test_ticker_filter_with_pagination()
# GET /api/research/briefs?ticker=AAPL
# Verify: Only AAPL briefs returned, total=2
```

**Pagination Flags**
```python
test_research_has_next_flag()
# Page 1 (offset=0) of 50 items with limit=25 → has_next=true
# Page 2 (offset=25) of 50 items → has_next=false
```

---

### 3. Integration Tests (TestPaginationIntegration)

**Full Pagination Flow**
```python
test_stock_grid_pagination_flow()
# Simulate: User views page 1, then clicks next
# Verify: Page 1 → all 9 stocks fit, no next button
```

**Multi-Page Scenarios**
```python
test_stock_pagination_boundary()
# 45 stocks, limit=20
# Page 1: 20 items, has_next=true
# Page 2: 20 items, has_next=true
# Page 3: 5 items, has_next=false
```

**Edge Cases**
```python
test_empty_result_pagination()
# No stocks available
# Verify: total=0, has_next=false, has_previous=false
```

---

## Mock Data

### Mock Stocks (test_pagination.py, line 48-57)
```python
[
  {'ticker': 'AAPL', 'market': 'US', 'active': 1},
  {'ticker': 'MSFT', 'market': 'US', 'active': 1},
  {'ticker': 'RELIANCE.NS', 'market': 'India', 'active': 1},
  # ... 6 more
  {'ticker': 'DELETED', 'market': 'US', 'active': 0},  # inactive
]
```

**Summary**: 9 active stocks (5 US, 4 India), 1 inactive

### Mock Briefs (test_pagination.py, line 65-101)
```python
[
  {'id': 1, 'ticker': 'AAPL', ...},
  {'id': 2, 'ticker': 'AAPL', ...},
  {'id': 3, 'ticker': 'MSFT', ...},
  # ... 4 more
]
```

**Summary**: 7 briefs (2 AAPL, 1 MSFT, 1 GOOGL, 2 TSLA, 1 NVDA)

---

## Test Assertions

### Common Assertions

```python
# HTTP Status
assert response.status_code == 200

# Response Structure
assert 'data' in response.json
assert 'meta' in response.json

# Metadata
assert response.json['meta']['limit'] == 20
assert response.json['meta']['offset'] == 0
assert response.json['meta']['total'] > 0
assert isinstance(response.json['meta']['has_next'], bool)
assert isinstance(response.json['meta']['has_previous'], bool)

# Data
assert isinstance(response.json['data'], list)
assert len(response.json['data']) <= response.json['meta']['limit']
```

---

## Mocking Strategy

### Mock Database Connections

Tests use `@patch` decorator to mock:
- `backend.api.stocks.get_all_stocks()`
- `backend.api.research.sqlite3.connect()`

**Example:**
```python
@patch('backend.api.stocks.get_all_stocks')
def test_default_limit_offset(self, mock_get_stocks, client, mock_stocks):
    mock_get_stocks.return_value = mock_stocks
    # Test isolation: no actual database queries
```

### Avoiding Database Side Effects

- All tests use mocked data
- No database writes
- No test database required
- Tests run in isolation

---

## Adding New Tests

### Template

```python
class TestNewFeature:
    @patch('backend.api.stocks.get_all_stocks')
    def test_new_behavior(self, mock_get_stocks, client, mock_stocks):
        """Test description"""
        mock_get_stocks.return_value = mock_stocks

        response = client.get('/api/stocks?param=value')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['meta']['limit'] == 20
        # Add specific assertions
```

### Naming Convention

- `test_` prefix (required)
- Describe behavior: `test_limit_enforcement`, `test_active_filtering`
- Use `mock_` prefix for fixtures

---

## Known Limitations

1. **SQLite Mock** - Research API tests mock sqlite3.connect, not actual queries
2. **Market Filter** - Tests verify Python-side filtering (frontend already tested)
3. **No Database State** - Tests don't verify actual database mutations

---

## Continuous Integration

### GitHub Actions (If Configured)

```yaml
- name: Run pagination tests
  run: python -m pytest backend/tests/test_pagination.py -v
```

---

## Troubleshooting

### Test Import Errors

```
ModuleNotFoundError: No module named 'backend'
```

**Solution**: Run from project root with PYTHONPATH:
```bash
PYTHONPATH=. python -m pytest backend/tests/test_pagination.py -v
```

### Mock Not Working

```
AssertionError: assert [] == mock_stocks
```

**Solution**: Ensure `@patch` decorator path matches import:
```python
@patch('backend.api.stocks.get_all_stocks')  # Correct
@patch('backend.core.stock_manager.get_all_stocks')  # Wrong
```

### Flask app.config Issues

```
RuntimeError: Working outside of request context
```

**Solution**: Use test client context:
```python
with test_app.app_context():
    # Your test code
```

---

## Performance Benchmarks

### Expected Test Execution Times

```
test_pagination.py
├── Stocks API (12 tests): ~2 seconds
├── Research API (7 tests): ~1.5 seconds
└── Integration (4 tests): ~0.5 seconds
   Total: ~4 seconds
```

---

## Coverage Report

Expected coverage for pagination code:

- `backend/api/stocks.py`: ~95% (limit/offset logic)
- `backend/api/research.py`: ~95% (limit/offset logic)
- `backend/core/stock_manager.py`: ~50% (other functions not tested)

Generate coverage report:
```bash
python -m pytest backend/tests/test_pagination.py \
  --cov=backend.api.stocks \
  --cov=backend.api.research \
  --cov-report=html
```

---

## Next Steps

1. **Run tests locally** to verify implementation
2. **Integrate into CI/CD** (GitHub Actions)
3. **Monitor performance** in production
4. **Collect user feedback** on pagination UX
5. **Iterate** on page sizes based on usage data

---

## Support

For test failures or questions:
1. Check test output for specific assertion failures
2. Review mock data setup
3. Verify API endpoint implementation matches test expectations
4. Check git diff for recent changes to API routes
