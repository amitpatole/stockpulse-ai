# API Validation & Error Handling Guide

**Version**: 1.0
**Last Updated**: 2026-03-03
**Status**: Complete validation framework in place

## Overview

TickerPulse AI implements a comprehensive validation layer for all API endpoints. This ensures:

- ✅ **Type Safety** - All inputs validated against Pydantic models
- ✅ **Consistent Error Responses** - Standardized error format across all endpoints
- ✅ **Input Validation** - Range checks, format validation, custom validators
- ✅ **Clear Error Messages** - Validation errors show exactly what's wrong

---

## Architecture

### Three-Layer Validation System

```
Request
   ↓
[1] Pydantic Model Validation (frontend: type, range, format)
   ↓
[2] Validation Functions (backend: custom logic, DB checks)
   ↓
[3] Error Handlers (Flask: standardized response)
   ↓
Response
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Request Models** | `backend/models/requests.py` | POST/PUT/DELETE request bodies |
| **Query Params** | `backend/models/query_params.py` | GET query parameters |
| **Validation** | `backend/core/validation.py` | Parsing helpers and type conversion |
| **Error Handling** | `backend/core/errors.py` | Custom exceptions and Flask handlers |

---

## Standard Error Response Format

All validation errors follow this format:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "status_code": 400,
  "details": {
    "ticker": "Ticker must be alphanumeric",
    "limit": "ensure this value is less than or equal to 100"
  },
  "timestamp": "2026-03-03T12:34:56.789Z"
}
```

### Error Codes

| Code | HTTP | Meaning | Example |
|------|------|---------|---------|
| `VALIDATION_ERROR` | 400 | Invalid input data | Missing field, wrong type |
| `INVALID_JSON` | 400 | Malformed JSON | `{"ticker": AAPL}` (missing quotes) |
| `NOT_FOUND` | 404 | Resource not found | Ticker doesn't exist |
| `UNAUTHORIZED` | 401 | Authentication required | Missing API key |
| `FORBIDDEN` | 403 | Permission denied | User can't access resource |
| `CONFLICT` | 409 | State conflict | Duplicate entry |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Rate limit hit |
| `DATABASE_ERROR` | 500 | Database failure | Connection lost |
| `EXTERNAL_SERVICE_ERROR` | 502 | External API failed | Yahoo Finance down |
| `INTERNAL_ERROR` | 500 | Server error | Unexpected exception |

---

## How to Use: Request Body Validation

### Step 1: Choose a Model

For POST/PUT/DELETE endpoints, use models from `backend/models/requests.py`:

```python
from backend.models.requests import StockCreateRequest
from backend.core.validation import get_request_body
```

### Step 2: Use `get_request_body()` in Your Endpoint

```python
@stocks_bp.route('/stocks', methods=['POST'])
def add_stock_endpoint():
    """Add a stock to watchlist.

    Request Body:
        ticker (str): Stock symbol (required, 1-5 chars, alphanumeric)
        name (str): Company name (optional)
        market (str): Market code (optional, default: 'US')
    """
    data = get_request_body(StockCreateRequest)
    # data is now a StockCreateRequest instance, fully validated

    ticker = data.ticker  # Already uppercase
    name = data.name
    market = data.market or 'US'

    # ... rest of logic
    return jsonify({'success': True})
```

### What Gets Validated Automatically

Pydantic automatically validates:
- **Type** - Field must match declared type (str, int, etc.)
- **Required** - Fields without default are required
- **Length** - String length constraints (min_length, max_length)
- **Range** - Numeric constraints (ge, le, gt, lt)
- **Format** - Custom validators via @field_validator

### Error Handling

If validation fails, a `ValidationError` is raised automatically and returns 400 response with details.

---

## How to Use: Query Parameter Validation

### Step 1: Choose a Model

For GET endpoints, use models from `backend/models/query_params.py`:

```python
from backend.models.query_params import StockListParams
from backend.core.validation import get_query_params
```

### Step 2: Use `get_query_params()` in Your Endpoint

```python
@stocks_bp.route('/stocks', methods=['GET'])
def list_stocks():
    """List monitored stocks with pagination."""
    params = get_query_params(StockListParams)
    # params is now fully validated

    stocks = get_all_stocks()
    if params.market and params.market != 'All':
        stocks = [s for s in stocks if s['market'] == params.market]

    total = len(stocks)
    stocks = stocks[params.offset : params.offset + params.limit]

    return jsonify({
        'data': stocks,
        'meta': {
            'total': total,
            'limit': params.limit,
            'offset': params.offset,
            'has_next': (params.offset + params.limit) < total,
            'has_previous': params.offset > 0,
        }
    })
```

---

## Creating Custom Request Models

```python
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class MyRequest(BaseModel):
    """Validation for POST /api/my-endpoint."""

    # Required field
    name: str = Field(..., min_length=1, max_length=100)

    # Optional field
    description: Optional[str] = Field(None, max_length=500)

    # Numeric constraints
    priority: int = Field(default=1, ge=1, le=5)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Custom validation logic."""
        v = v.strip().title()
        if not v:
            raise ValueError('Name cannot be empty')
        return v
```

---

## Common Patterns

### Simple Pagination

```python
from backend.models.query_params import PaginationParams
from backend.core.validation import get_query_params

@app.get('/api/items')
def list_items():
    params = get_query_params(PaginationParams)
    items = fetch_all_items()
    total = len(items)
    items = items[params.offset : params.offset + params.limit]

    return jsonify({
        'data': items,
        'meta': {
            'total': total,
            'limit': params.limit,
            'offset': params.offset,
            'has_next': (params.offset + params.limit) < total,
            'has_previous': params.offset > 0,
        }
    })
```

### Filtering with Pagination

```python
from backend.models.query_params import StockListParams
from backend.core.validation import get_query_params

@app.get('/api/stocks')
def list_stocks():
    params = get_query_params(StockListParams)
    
    stocks = get_all_stocks()
    if params.market and params.market != 'All':
        stocks = [s for s in stocks if s['market'] == params.market]

    total = len(stocks)
    stocks = stocks[params.offset : params.offset + params.limit]

    return jsonify({
        'data': stocks,
        'meta': {
            'total': total,
            'limit': params.limit,
            'offset': params.offset,
            'has_next': (params.offset + params.limit) < total,
            'has_previous': params.offset > 0,
        }
    })
```

---

## Debugging

### Query parameter not converting from string?

Use `get_query_params()` which handles type conversion automatically:

```python
# ✅ Correct
params = get_query_params(PaginationParams)
limit = params.limit  # Already an int
```

### Custom validator not running?

Ensure `@field_validator` is the first decorator:

```python
# ✅ Correct order
@field_validator('ticker')
@classmethod
def validate_ticker(cls, v):
    return v.upper()
```

---

## Migration Checklist

For each API endpoint:

- [ ] Choose appropriate Pydantic model from `requests.py` or `query_params.py`
- [ ] Replace manual `request.json` with `get_request_body(Model)`
- [ ] Replace manual `request.args` with `get_query_params(Model)`
- [ ] Remove manual validation code
- [ ] Test with valid and invalid data
- [ ] Verify error response format matches standard

---

## Related Files

- `backend/core/errors.py` - Exception classes and Flask error handlers
- `backend/core/validation.py` - Helper functions (get_request_body, get_query_params)
- `backend/models/requests.py` - POST/PUT/DELETE request models
- `backend/models/query_params.py` - GET query parameter models
