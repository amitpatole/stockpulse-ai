# Technical Design: Input Validation & Error Handling

## Approach

Implement **Pydantic v2** models for input validation at API boundaries, with a **unified error response format** enforced via Flask middleware. Three layers:

1. **Request Models**: Pydantic models for each endpoint's input schema
2. **Global Error Handler**: Intercepts validation failures and returns consistent `{data, meta, errors}` format
3. **Response Wrapper**: Utility to enforce response shape across all endpoints

This aligns with CLAUDE.md spec (API returns `{data, meta, errors}`), eliminates manual `try/except` blocks, and provides client-friendly error messages with field-level validation details.

---

## Files to Modify/Create

### New Files
- **`backend/core/validation.py`**: Pydantic base models, custom validators, shared types
  - `BaseRequest` (abstract base with common fields)
  - `PaginationParams` (limit, offset with max bounds)
  - `ErrorResponse` (field-level errors array)
  - Custom validators: ticker format, market codes, numeric ranges

- **`backend/core/response.py`**: Response wrapper utilities
  - `APIResponse` dataclass with `data`, `meta`, `errors` fields
  - `success(data, meta={})` → returns `{data, meta, errors: None}`
  - `error(errors, status_code=400)` → returns `{data: None, meta: {}, errors}`
  - `paginated(data, total, limit, offset, errors=None)` → full pagination response

- **`backend/api/validators.py`**: Per-endpoint request models
  - `AddStockRequest` (ticker, name, market)
  - `SearchStockRequest` (q: string, min_length=1)
  - `ListResearchBriefsRequest` (ticker, limit, offset)
  - `AddAlertRequest` (ticker, threshold, alert_type)
  - `SettingsRequest` (provider, api_key, model)

### Modified Files
- **`backend/app.py`**:
  - Register `@app.errorhandler(pydantic.ValidationError)` → `{errors: [field, message]}`
  - Register generic 400/404/500 handlers → consistent error format
  - Add `CORS` headers to error responses

- **`backend/api/stocks.py`, `research.py`, `settings.py`, etc.**:
  - Replace manual `request.args.get()` + try/except with Pydantic model parsing
  - Use `APIResponse.success()` / `APIResponse.error()` for all returns
  - Simplify endpoint logic: validation → business logic → response

- **`requirements.txt`**:
  - Add `pydantic>=2.0.0` (for v2 validation syntax)

---

## Data Model Changes

**None** — validation is orthogonal to database schema.

---

## API Changes

### Before (Inconsistent)
```bash
# Stocks endpoint returns {success, error}
POST /api/stocks
{"success": false, "error": "Missing required field: ticker"}

# Research endpoint returns {data, meta}
GET /api/research/briefs
{"data": [...], "meta": {...}}
```

### After (Unified)
```bash
# All endpoints return {data, meta, errors}

# Validation error → 400
POST /api/stocks
{
  "data": null,
  "meta": {},
  "errors": [
    {"field": "ticker", "message": "Ticker must be 1-5 uppercase letters"}
  ]
}

# Success → 200
POST /api/stocks
{
  "data": {"ticker": "AAPL", "name": "Apple Inc.", "market": "US"},
  "meta": {},
  "errors": null
}

# List with pagination → 200
GET /api/research/briefs?limit=25&offset=0
{
  "data": [{"id": 1, "ticker": "AAPL", ...}],
  "meta": {
    "total": 150,
    "limit": 25,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  },
  "errors": null
}
```

### Affected Endpoints
- All 10+ endpoints in `/api/stocks`, `/api/research`, `/api/settings`, `/api/agents`, `/api/analysis`
- Changes: Response wrapper only (no new endpoints)

---

## Frontend Changes

**Minimal** — Response structure already aligns:
- Current code handles `{data, meta}` format
- Add null-check for `errors` field before rendering
- Validation errors already displayed from error responses (no new UI logic needed)

---

## Testing Strategy

### Unit Tests (`backend/tests/test_validation.py`)
- **Validators**: Test Pydantic models with valid/invalid inputs
  - Valid: `{"ticker": "AAPL"}` → parses successfully
  - Invalid: `{"ticker": "AAPL123"}` → validation error with message
  - Edge cases: empty strings, out-of-range integers, missing required fields

- **Response wrappers**: Test `APIResponse.success()` / `.error()` format
  - Success wraps data in `{data, meta, errors: null}`
  - Error returns `{data: null, errors: [...]}`
  - Pagination includes `has_next`, `has_previous`

### Integration Tests (`backend/tests/test_api_validation.py`)
- **Endpoint validation**: POST /api/stocks with missing `ticker` → 400 with error details
- **Pagination validation**: GET /api/research/briefs?limit=999 → clamped to max=100
- **Success path**: POST /api/stocks with valid data → 200 with wrapped response
- **Error handler coverage**: 400/404/500 responses use unified format

### E2E Tests (Playwright)
- Frontend displays validation errors from `errors` field (no new test needed if already tested error states)
- No breaking changes to existing flow tests

### Coverage Goals
- 100% of validation models tested (happy + error + edge cases)
- All error response formats verified
- At least 3 endpoints per module (stocks, research, settings)

---

## Rollout Sequence

1. Create `validation.py` (base models) + `response.py` (wrappers)
2. Create `validators.py` (per-endpoint models)
3. Register error handlers in `app.py`
4. Migrate endpoints one-by-one (stocks → research → settings → agents)
5. Add test coverage for each migrated endpoint
6. Remove old manual validation code

---

## Acceptance Criteria

- ✅ All API endpoints return `{data, meta, errors}` format
- ✅ Validation errors include field name + human-readable message
- ✅ HTTP status codes: 200 (success), 400 (validation), 404 (not found), 500 (server error)
- ✅ Endpoint code simplified: validation → business logic → response (no try/except boilerplate)
- ✅ 30+ tests covering validators, response wrappers, endpoint integration
- ✅ Frontend rendering works without changes (backwards compatible)
