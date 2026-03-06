# API Test Quick Start Guide

A quick reference for running and understanding the focused API endpoint test suites.

---

## One-Liner: Run All Tests

```bash
PYTHONPATH=. pytest backend/tests/test_api_*_focused.py -v --tb=short
```

---

## Test Files Overview

### 1. Analysis API Tests
**File**: `backend/tests/test_api_analysis_focused.py` (10 tests)

Tests for:
- GET `/api/ai/ratings` - AI ratings with period/limit validation
- GET `/api/chart/<ticker>` - Historical price data with period validation

**Key Tests**:
```python
# Period validation: must be 1-252
test_get_ai_ratings_period_validation_out_of_range()

# Currency detection: USD vs INR
test_get_chart_data_currency_detection()
```

**Run**: `pytest backend/tests/test_api_analysis_focused.py -v`

---

### 2. Stocks API Tests
**File**: `backend/tests/test_api_stocks_focused.py` (16 tests)

Tests for:
- GET `/api/stocks/search` - Ticker/company search via Yahoo Finance
- POST `/api/stocks` - Add new stocks with validation
- GET `/api/stocks` - List monitored stocks with pagination/filtering

**Key Tests**:
```python
# Empty search query handling
test_search_stocks_empty_query_returns_empty()

# Ticker not found with suggestions
test_add_stock_ticker_not_found_with_suggestions()

# Pagination & filtering
test_get_stocks_market_filter()
```

**Run**: `pytest backend/tests/test_api_stocks_focused.py -v`

---

### 3. Research API Tests
**File**: `backend/tests/test_api_research_focused.py` (10 tests)

Tests for:
- GET `/api/research/briefs` - List briefs with pagination/filtering
- POST `/api/research/briefs` - Generate new research briefs

**Key Tests**:
```python
# Pagination metadata
test_list_briefs_pagination_metadata()

# Random ticker selection from watchlist
test_generate_brief_random_ticker_from_watchlist()
```

**Run**: `pytest backend/tests/test_api_research_focused.py -v`

---

## Test Structure (Pattern)

All focused tests follow this proven pattern:

```python
import pytest
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def test_app():
    """Create Flask test app."""
    from backend.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(test_app):
    """Flask test client."""
    return test_app.test_client()

class TestEndpoint:
    """Test [endpoint] endpoint."""

    def test_happy_path(self, client):
        """AC1: Happy path description."""
        with patch('backend.api.module.dependency') as mock:
            mock.return_value = test_data
            response = client.get('/api/endpoint')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['field'] == expected_value
```

### Key Elements:

1. **Fixture**: Reusable test setup (app, client, mock data)
2. **Mock Pattern**: `with patch(...)` for isolation
3. **Assertion**: Clear `assert` statements
4. **Naming**: Test names describe what is tested (not `test_1`)

---

## Common Test Scenarios

### Test API Response Status
```python
def test_endpoint_returns_200(self, client):
    response = client.get('/api/endpoint')
    assert response.status_code == 200
```

### Test Response Structure
```python
def test_endpoint_returns_json_structure(self, client):
    response = client.get('/api/endpoint')
    data = json.loads(response.data)
    assert 'data' in data
    assert 'meta' in data
```

### Test Validation Error (400)
```python
def test_endpoint_rejects_invalid_input(self, client):
    response = client.post('/api/endpoint', json={'bad': 'data'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
```

### Test Not Found (404)
```python
def test_endpoint_not_found(self, client):
    response = client.get('/api/endpoint/NONEXISTENT')
    assert response.status_code == 404
```

### Test with Mocked Database
```python
def test_with_database_mock(self, client):
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = [...]
        mock_connect.return_value = mock_conn

        response = client.get('/api/endpoint')
        assert response.status_code == 200
```

### Test with Mocked External Service
```python
def test_with_external_service(self, client):
    with patch('backend.api.module.external_service') as mock:
        mock.return_value = {'result': 'data'}
        response = client.post('/api/endpoint')
        assert response.status_code == 200
```

---

## Debugging Failing Tests

### 1. Check Test Output
```bash
pytest backend/tests/test_api_analysis_focused.py::TestAIRatingsEndpoint::test_get_ai_ratings_happy_path -v -s
```
- `-v` = verbose
- `-s` = show print statements

### 2. Check Mock Calls
```python
def test_debug_mock(self, client):
    with patch('backend.api.module.func') as mock:
        # Do something
        mock.assert_called_once()  # Verify called
        print(mock.call_args)      # See what args were passed
```

### 3. Check Response Body
```python
def test_debug_response(self, client):
    response = client.get('/api/endpoint')
    print(response.data)  # Print raw response
    print(json.loads(response.data))  # Pretty-print JSON
```

---

## Test Coverage by Endpoint

| Endpoint | Tests | Coverage |
|----------|-------|----------|
| GET /api/ai/ratings | 5 | Period validation, default behavior |
| GET /api/chart/<ticker> | 5 | Period validation, currency, no data |
| GET /api/stocks/search | 5 | Empty query, ticker search, no results |
| POST /api/stocks | 6 | Add, validation, suggestions, lookup |
| GET /api/stocks | 5 | Filter, pagination, active check, market |
| GET /api/research/briefs | 6 | Pagination, filtering, metadata |
| POST /api/research/briefs | 4 | Generate, random, default ticker |
| **Total** | **36** | **Comprehensive** |

---

## Pre-Commit Hook Integration

These tests can be run before commits:

```bash
# In .git/hooks/pre-commit
#!/bin/bash
PYTHONPATH=. pytest backend/tests/test_api_*_focused.py -q || exit 1
```

---

## CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Run API Tests
  run: |
    pip install -r requirements.txt
    PYTHONPATH=. pytest backend/tests/test_api_*_focused.py -v --tb=short
```

---

## Tips & Best Practices

✅ **DO**:
- Use fixtures for reusable data
- Mock external dependencies
- One assertion per behavior
- Name tests to describe what they test
- Use parametrize for multiple similar cases

❌ **DON'T**:
- Use hardcoded test data in tests
- Test multiple endpoints in one test
- Use console.log / print statements
- Skip tests or mark as xfail
- Create real database/API calls

---

## Contact & Support

Questions about specific tests? Check the test docstring:
```bash
grep -A5 "def test_get_ai_ratings_period_validation" backend/tests/test_api_analysis_focused.py
```

All tests follow the same pattern for consistency and clarity.

---

**Last Updated**: 2026-03-03
**Status**: Ready to use
**Maintainer**: QA Team (Jordan Blake)
