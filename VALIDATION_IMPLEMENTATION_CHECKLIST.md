# Validation Implementation Checklist

Use this checklist when adding Pydantic validation to existing or new endpoints.

## Pre-Implementation

- [ ] Read `docs/API_VALIDATION_GUIDE.md` for endpoint requirements
- [ ] Identify request parameters (body, query, path)
- [ ] Check if appropriate request model exists in `backend/models/requests.py`
- [ ] Check if response model exists in `backend/models/responses.py`
- [ ] Create new models if needed

## Implementation

### Step 1: Add Imports
- [ ] Import Pydantic request model(s)
- [ ] Import validation helpers: `get_request_body`, `get_query_params`
- [ ] Import custom exceptions if needed: `NotFoundError`, `ConflictError`, etc.

```python
from backend.models import StockCreateRequest, PaginationParams
from backend.core.validation import get_request_body, get_query_params
from backend.core.errors import NotFoundError
```

### Step 2: Replace Manual Validation

**For Request Body:**
- [ ] Remove manual `request.get_json()` calls
- [ ] Remove manual `data.get('field', default)` calls
- [ ] Remove manual validation checks (type, range, format)
- [ ] Replace with `data = get_request_body(StockCreateRequest)`

**For Query Parameters:**
- [ ] Remove manual `request.args.get()` calls
- [ ] Remove manual type conversions (int(), bool())
- [ ] Remove manual range checks
- [ ] Replace with `params = get_query_params(PaginationParams)`

**For Path Parameters:**
- [ ] Path validation is automatic from Flask routing
- [ ] Can use `get_path_param('name', type)` if additional validation needed

### Step 3: Remove Conditional Checks

**Remove these patterns:**
```python
# ❌ BEFORE: Manual validation
data = request.get_json()
if not data or 'ticker' not in data:
    return {"error": "ticker is required"}, 400
ticker = data['ticker'].upper()
if not ticker.isalnum():
    return {"error": "invalid ticker"}, 400
if len(ticker) > 5:
    return {"error": "ticker too long"}, 400

# ✅ AFTER: Automatic validation
data = get_request_body(StockCreateRequest)
ticker = data.ticker  # Already validated
```

### Step 4: Add Business Logic Error Handling

- [ ] Replace 404 dict responses with `raise NotFoundError(...)`
- [ ] Replace 409 dict responses with `raise ConflictError(...)`
- [ ] Replace 400 dict responses with `raise ValidationError(...)`
- [ ] Let Flask error handlers convert to JSON responses

```python
# ❌ BEFORE: Manual error responses
if not stock:
    return {"error": "not found"}, 404

# ✅ AFTER: Custom exceptions
if not stock:
    raise NotFoundError(f"Stock {ticker} not found")
```

### Step 5: Document with Response Models

- [ ] Import response model if available
- [ ] Ensure response matches model schema (types, fields)
- [ ] Update docstring with request/response examples
- [ ] Reference validation rules from model

```python
from backend.models import StockResponse, PaginatedResponse

@app.get('/api/stocks')
def list_stocks():
    """
    List all stocks with pagination.

    Query Parameters:
        limit (int): Items per page (1-100, default 20)
        offset (int): Pagination offset (default 0)

    Returns (200):
        {
            "data": [StockResponse, ...],
            "meta": {
                "total": int,
                "limit": int,
                "offset": int,
                "has_next": bool,
                "has_previous": bool
            }
        }
    """
    params = get_query_params(PaginationParams)
    # ...
```

## Testing

### Unit Tests

- [ ] Test valid request succeeds
- [ ] Test missing required field fails (400)
- [ ] Test invalid field value fails (400)
- [ ] Test out-of-range value fails (400)
- [ ] Test type mismatch fails (400)
- [ ] Test business logic errors (404, 409, etc.)

```python
def test_create_stock_success(client):
    response = client.post('/api/stocks', json={
        "ticker": "AAPL",
        "name": "Apple Inc."
    })
    assert response.status_code == 201
    assert response.json['success'] is True


def test_create_stock_invalid_ticker(client):
    response = client.post('/api/stocks', json={
        "ticker": "INVALID TICKER"
    })
    assert response.status_code == 400
    assert response.json['error'] == 'VALIDATION_ERROR'
    assert 'ticker' in response.json['details']


def test_get_stock_not_found(client):
    response = client.get('/api/stocks/NOTEXIST')
    assert response.status_code == 404
    assert response.json['error'] == 'NOT_FOUND'
```

### Manual Testing

```bash
# Valid request
curl -X POST http://localhost:5000/api/stocks \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "name": "Apple Inc."}'

# Invalid request (validation error)
curl -X POST http://localhost:5000/api/stocks \
  -H "Content-Type: application/json" \
  -d '{"ticker": "INVALID TICKER"}'

# Query parameters
curl "http://localhost:5000/api/stocks?limit=20&offset=0"

# Invalid query parameters
curl "http://localhost:5000/api/stocks?limit=200"  # max is 100
```

## Code Review Checklist

- [ ] Request models are used for all inputs
- [ ] No manual validation logic in endpoints
- [ ] Error responses use custom exceptions, not dict returns
- [ ] Error handlers registered in `app.py`
- [ ] Response types match documented models
- [ ] Tests cover validation boundaries
- [ ] Type hints are present (Pydantic models)
- [ ] No hardcoded validation rules (use models)
- [ ] Error messages are user-friendly
- [ ] Edge cases handled (empty strings, None, etc.)

## Common Pitfalls to Avoid

### ❌ Don't

```python
# Manual validation still in code
@app.post('/api/stocks')
def create_stock():
    data = request.get_json()
    if not data or 'ticker' not in data:
        return {"error": "missing ticker"}, 400
    # ...

# Manual error responses
if not stock:
    return {"error": "not found"}, 404

# Missing error handler imports
@app.errorhandler(ValidationError)  # Wrong!

# Inconsistent response formats
return {"ok": True}  # Should use {"success": True}
return {"message": "error"}  # Should use {"error": "...", "message": "..."}
```

### ✅ Do

```python
# Automatic validation
@app.post('/api/stocks')
def create_stock():
    data = get_request_body(StockCreateRequest)
    # data is already validated
    # ...

# Custom exceptions
if not stock:
    raise NotFoundError(f"Stock {ticker} not found")

# Pre-registered error handlers
register_error_handlers(app)  # Already done in app.py

# Consistent responses
return {"success": True}
raise NotFoundError(message="Stock not found")
```

## Quick Reference: Error Status Codes

| Exception | Status | Code | When to Use |
|-----------|--------|------|------------|
| `ValidationError` | 400 | `VALIDATION_ERROR` | Input validation fails |
| `NotFoundError` | 404 | `NOT_FOUND` | Resource doesn't exist |
| `UnauthorizedError` | 401 | `UNAUTHORIZED` | Auth required |
| `ForbiddenError` | 403 | `FORBIDDEN` | Permission denied |
| `ConflictError` | 409 | `CONFLICT` | State conflict (duplicate, etc.) |
| `RateLimitError` | 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| `ExternalServiceError` | 502 | `EXTERNAL_SERVICE_ERROR` | External API failed |
| `DatabaseError` | 500 | `DATABASE_ERROR` | DB operation failed |

## Model Selection Guide

### Request Models

| Model | When to Use | Example |
|-------|------------|---------|
| `PaginationParams` | List endpoints | GET /api/stocks |
| `ResearchPaginationParams` | Research lists | GET /api/research/briefs |
| `AgentPaginationParams` | Agent history | GET /api/agents/runs |
| `StockCreateRequest` | Creating stocks | POST /api/stocks |
| `StockSearchRequest` | Searching | GET /api/stocks/search?q=... |
| `ChatRequest` | Chat operations | POST /api/chat/ask |
| `RatingsRequest` | Rating queries | GET /api/ai/ratings |
| `ChartRequest` | Price data | GET /api/chart/... |

### Response Models

| Model | When to Use | Example |
|-------|------------|---------|
| `PaginatedResponse[T]` | Paginated lists | GET /api/stocks |
| `StockResponse` | Stock object | Any stock endpoint |
| `ResearchBriefResponse` | Research brief | GET /api/research/briefs |
| `RatingResponse` | Stock rating | GET /api/ai/ratings |
| `ChatResponse` | Chat response | POST /api/chat/ask |
| `ErrorResponse` | Error (automatic) | Any error response |
| `SuccessResponse` | Generic success | Simple success responses |

## Examples by Endpoint Type

### Simple GET Endpoint

```python
@app.get('/api/agents/<agent_name>')
def get_agent(agent_name):
    """Get agent details."""
    agent = find_agent(agent_name)
    if not agent:
        raise NotFoundError(f"Agent {agent_name} not found")
    return AgentResponse(**agent).model_dump()
```

### Paginated LIST Endpoint

```python
@app.get('/api/stocks')
def list_stocks():
    """List stocks with pagination."""
    params = get_query_params(PaginationParams)
    stocks = fetch_stocks(limit=params.limit, offset=params.offset)
    total = count_stocks()

    return PaginatedResponse(
        data=[StockResponse(**s).model_dump() for s in stocks],
        meta={"total": total, "limit": params.limit, ...}
    ).model_dump()
```

### Create (POST) Endpoint

```python
@app.post('/api/stocks')
def create_stock():
    """Create new stock."""
    data = get_request_body(StockCreateRequest)

    if database.find_stock(data.ticker):
        raise ConflictError(f"Stock {data.ticker} already exists")

    stock = database.create_stock(**data.model_dump())
    return StockCreateResponse(**stock).model_dump(), 201
```

### Query with Filters

```python
@app.get('/api/agents')
def list_agents():
    """List agents with optional filters."""
    params = get_query_params(AgentFiltersRequest)

    agents = fetch_agents(
        category=params.category,
        enabled=params.enabled
    )

    return {
        "agents": [AgentResponse(**a).model_dump() for a in agents],
        "total": len(agents)
    }
```

## Validation Rules Reference

### Pagination
- `limit`: `1 <= limit <= 100` (default 20)
- `offset`: `offset >= 0` (default 0)

### Stocks
- `ticker`: `1 <= len <= 5`, alphanumeric, uppercase
- `name`: `0 <= len <= 255`

### Analysis
- `period`: `1 <= period <= 252` (days)
- `limit`: `1 <= limit <= 1000`
- Chart period: one of `['1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max']`

### Chat
- `ticker`: Same as stocks
- `question`: `1 <= len <= 1000`
- `thinking_level`: one of `['quick', 'balanced', 'deep']`

### Settings
- `provider`: one of `['anthropic', 'openai', 'google_ai', 'xai']`
- `api_key`: non-empty string
- `framework`: one of `['crewai', 'openclaw']`

## Documentation Links

- [API Validation Guide](docs/API_VALIDATION_GUIDE.md) - Complete guide
- [Input Validation Summary](docs/INPUT_VALIDATION_SUMMARY.md) - Technical details
- [Pydantic Docs](https://docs.pydantic.dev/) - External reference
- [Flask Error Handling](https://flask.palletsprojects.com/errorhandling/) - Flask reference

---

**Last Updated**: 2026-03-03
**Version**: 1.0
