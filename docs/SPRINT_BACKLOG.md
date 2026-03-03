# Sprint Backlog: TickerPulse Checkout v3.2.2+

**Last Updated**: 2026-03-05
**Status**: Ready for Sprint Planning
**Total Capacity**: 48 story points over 6 sprints (8 pts/sprint target)

---

## CRITICAL Priority (Fix Before Shipping)

### 1. Fix Import Path Errors in ai_analytics.py

**User Story**
As a **backend developer**, I want to fix incorrect module imports in `ai_analytics.py`, so that AI analytics functions don't crash at runtime with `ModuleNotFoundError`.

**Acceptance Criteria**
- [ ] Lines 464-465 in `backend/core/ai_analytics.py` updated to use correct import paths (`backend.core.settings_manager` and `backend.core.ai_providers`)
- [ ] All AI analytics functions execute without import errors (verified by running unit tests for `ai_analytics.py`)
- [ ] No `ModuleNotFoundError` in logs when accessing analytics endpoints

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
CRITICAL because this is a runtime blocker that will crash the application whenever AI analytics code is executed.

**Complexity**
1 point | Single file fix, straightforward import path correction


---

### 2. Fix API Key Exposure in Logs

**User Story**
As a **security engineer**, I want to mask API keys in all log output, so that sensitive credentials are never exposed in logs or debugging output.

**Acceptance Criteria**
- [ ] Create `_mask_api_key()` utility function that masks all but first 4 and last 4 characters (e.g., `"sk_live_xxxxx...1234"`)
- [ ] Update `backend/api/settings.py` (line 158+) to mask API key before any logging
- [ ] Update `backend/core/ai_providers.py` to use masked key in debug logs
- [ ] Verify logs contain no unmasked API keys (scan logs for full API key patterns)

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
CRITICAL because unmasked API keys in logs create security vulnerabilities and compliance violations.

**Complexity**
2 points | Small utility function + updates to 3 files, straightforward masking logic


---

### 3. Fix Hardcoded SECRET_KEY in config.py

**User Story**
As a **DevOps engineer**, I want to ensure `SECRET_KEY` is always loaded from environment variables with no fallback default, so that sessions are secure in production.

**Acceptance Criteria**
- [ ] Remove the hardcoded default value from `backend/config.py` line 27
- [ ] Raise `ValueError` with clear message if `SECRET_KEY` environment variable is not set
- [ ] Document required environment variables in `docs/DEPLOYMENT.md`
- [ ] Verify CI/CD fails with helpful error if SECRET_KEY is missing

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
CRITICAL because hardcoded fallback defeats security in production if env var is accidentally missing.

**Complexity**
1 point | Single file change + error handling, minimal dependencies


---

### 4. Add Input Validation to API Endpoints

**User Story**
As a **quality assurance engineer**, I want all API endpoints to validate query parameters (period, limit, ticker), so that invalid data cannot be accepted or processed.

**Acceptance Criteria**
- [ ] `GET /api/analysis/period-analysis/<ticker>`: validate `period` against whitelist `['1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max']`, return 400 if invalid
- [ ] `GET /api/research/briefs`: validate `limit` is integer between 1-200, return 400 if invalid
- [ ] `GET /api/stocks/search`: validate `ticker` is alphanumeric (A-Z, 0-9) max 5 chars, return 400 if invalid
- [ ] All invalid requests return 400 with clear error message specifying allowed values
- [ ] Automated tests verify all invalid inputs are rejected (5+ test cases per endpoint)

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
CRITICAL because invalid input can corrupt financial data calculations and confuse users.

**Complexity**
3 points | Updates to 3+ endpoints, validation logic, test coverage


---

### 5. Add Error Boundary Component to Frontend

**User Story**
As a **frontend developer**, I want to add an Error Boundary component to wrap the React app, so that JavaScript errors don't crash the entire page.

**Acceptance Criteria**
- [ ] Create `ErrorBoundary.tsx` component that catches all JavaScript errors in child components
- [ ] Error boundary displays user-friendly message when error occurs (not technical stack trace)
- [ ] Error details are logged with context (timestamp, user_id, URL) for debugging
- [ ] Component can recover from errors when page is refreshed
- [ ] Unit tests verify error catching and recovery behavior

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
CRITICAL because unhandled JavaScript errors create poor user experience and hide real issues.

**Complexity**
2 points | New component, React lifecycle methods, logging integration

---

## HIGH Priority (Next 2 Sprints)

### 6. Add Type Hints Coverage from 30% to 95%

**User Story**
As a **code quality engineer**, I want to increase type hint coverage from 30% to 95% across all backend modules, so that developers catch type errors early and improve code clarity.

**Acceptance Criteria**
- [ ] Run `mypy --strict` across all backend modules and document baseline (currently ~30%)
- [ ] Add type hints to all function signatures in `backend/core/`, `backend/api/`, `backend/models/`
- [ ] Add return type hints to all functions (no implicit `None` returns)
- [ ] Target 95%+ coverage verified by mypy in strict mode
- [ ] mypy passes in CI/CD pipeline with no errors or warnings

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
HIGH because type errors cause production bugs and poor developer experience. Strong typing catches errors early.

**Complexity**
5 points | Affects 40+ files, significant effort across multiple modules


---

### 7. Refactor Complex Functions (ai_rating, generate_brief)

**User Story**
As a **backend developer**, I want to refactor `calculate_ai_rating()` (175 lines) and `_generate_sample_brief()` (148 lines) into smaller, testable functions, so that code is maintainable and bugs are easier to fix.

**Acceptance Criteria**
- [ ] Break `calculate_ai_rating()` into 4+ smaller functions: `_calculate_momentum_rating()`, `_calculate_trend_rating()`, `_aggregate_ratings()`
- [ ] Break `_generate_sample_brief()` into 3+ functions: `_format_section()`, `_apply_indicators()`, `_compile_brief()`
- [ ] Each function ≤40 lines, single responsibility, testable in isolation
- [ ] All new functions have type hints and docstrings
- [ ] Existing unit tests pass without modification (behavior unchanged)

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
HIGH because complex monolithic functions are hard to test, debug, and maintain. Reduces technical debt.

**Complexity**
5 points | Significant refactoring, careful testing to avoid behavioral changes


---

### 8. Implement Database Connection Pooling

**User Story**
As a **DevOps engineer**, I want to implement connection pooling for database operations, so that the application can handle concurrent requests efficiently without connection exhaustion.

**Acceptance Criteria**
- [ ] Add connection pool (max 10 connections) to `backend/models/database.py`
- [ ] All database operations use pooled connections (verify no direct `sqlite3.connect()` calls)
- [ ] Load test shows connection pool handles 50+ concurrent requests without timeouts
- [ ] Monitor connection pool utilization in logs (info level: pool size, active connections)
- [ ] Connection failures are caught and logged with retry logic

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
HIGH because current implementation can run out of connections under load, causing request failures.

**Complexity**
4 points | Database layer changes, integration testing, performance validation


---

### 9. Add Request Cancellation (AbortController) to Frontend

**User Story**
As a **frontend developer**, I want to implement `AbortController` for all fetch requests, so that pending API calls are cancelled when users navigate away or requests take too long.

**Acceptance Criteria**
- [ ] Add `AbortController` to `lib/api.ts` fetch wrapper
- [ ] Implement timeout logic: cancel requests after 30 seconds
- [ ] Cancel pending requests when user navigates to different page (cleanup in useEffect)
- [ ] Handle `AbortError` gracefully in error handling (don't show as generic error)
- [ ] Unit tests verify requests are cancelled and errors are handled correctly

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
HIGH because pending requests waste bandwidth and cause memory leaks when users navigate quickly.

**Complexity**
3 points | Wrapper function changes, cleanup logic, error handling


---

### 10. Implement Missing Technical Indicators

**User Story**
As a **product manager**, I want to implement all 10 promised technical indicators (RSI, MACD, Bollinger Bands, moving averages, etc.), so that users get the full feature set promised in the product.

**Acceptance Criteria**
- [ ] Implement 9 missing indicators: MACD, Bollinger Bands, Stochastic, EMA, SMA, ATR, CCI, ADX, VWAP
- [ ] Each indicator has unit tests verifying correctness against known datasets (e.g., test data for RSI=65 at specific date)
- [ ] API endpoint `/api/indicators/<ticker>?type=<indicator_type>` returns all 10 indicators
- [ ] Frontend displays all indicators on stock chart (lazy load if needed)
- [ ] Documentation updated with indicator definitions and calculation methods

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
HIGH because feature gap (1/10 indicators) is critical for product viability. Users expect promised features.

**Complexity**
8 points | 9 new algorithms, API endpoint, chart integration, documentation


---

### 11. Fix Settings Page Not Saving Changes

**User Story**
As a **frontend user**, I want to save changes to my settings (API key, preferences, theme) and have them persist, so that my configuration isn't lost on page reload.

**Acceptance Criteria**
- [ ] Settings form submission calls `PUT /api/settings` with user ID and changed fields
- [ ] Success shows green toast: "Settings saved successfully"
- [ ] Validation errors show in toast and fields are highlighted (e.g., "API key must be 32+ characters")
- [ ] Verify settings persist after page reload (check localStorage + backend API)
- [ ] Unit tests verify API call is made with correct payload and response is handled

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
HIGH because non-functional feature prevents users from configuring API keys and preferences.

**Complexity**
3 points | Form submission logic, API integration, validation + error handling


---

## MEDIUM Priority (Sprints 4-5)

### 12. Add Retry Logic to API Calls with Exponential Backoff

**User Story**
As a **reliability engineer**, I want to implement automatic retry logic for failed API calls, so that transient network failures don't immediately fail user requests.

**Acceptance Criteria**
- [ ] Create retry wrapper: `retryFetch(url, options, maxRetries=3, delayMs=100)`
- [ ] Implement exponential backoff: delay = 100ms * (2 ^ retry_count)
- [ ] Only retry on transient errors (5xx, timeouts) not permanent errors (4xx)
- [ ] Log each retry attempt with delay duration (info level)
- [ ] Unit tests verify retry count, delay timing, and error propagation

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
MEDIUM because network reliability is important but not blocking if requests eventually succeed.

**Complexity**
3 points | Wrapper function, exponential backoff math, error classification


---

### 13. Extract Hardcoded Constants to Configuration

**User Story**
As a **DevOps engineer**, I want to move hardcoded constants (RSI=14, MACD=26, rating thresholds=80/65/50/35) to a config file, so that values can be adjusted without redeploying code.

**Acceptance Criteria**
- [ ] Create `backend/config/constants.py` with all hardcoded values (RSI, MACD, EMA, SMA windows, rating thresholds)
- [ ] Load constants from environment variables with defaults (e.g., `RSI_WINDOW = int(os.getenv('RSI_WINDOW', 14))`)
- [ ] Update all references in `ai_analytics.py`, `indicators.py`, etc.
- [ ] Document all constants in `docs/CONFIGURATION.md` with allowed ranges
- [ ] Verify tests pass with different constant values

**Definition of Done**
- Code reviewed and merged
- Tests written and passing
- Acceptance criteria verified

**Priority**
MEDIUM because technical debt but not blocking. Improves flexibility without breaking functionality.

**Complexity**
3 points | Config file creation, refactoring references, environment variable handling


---

## Sprint Plan

| Sprint | Focus | Story Points | Target Items | Timeline |
|--------|-------|--------------|--------------|----------|
| **Sprint 1** | Critical Fixes | 8 | 1-4 (Import, API Key, SECRET_KEY, Input Validation) | Weeks 1-2 |
| **Sprint 2** | Frontend + Type Hints | 8 | 5-6 (Error Boundary, Type Hints) | Weeks 3-4 |
| **Sprint 3** | Refactoring + Pooling | 9 | 7-8 (Complex Functions, Connection Pooling) | Weeks 5-6 |
| **Sprint 4** | Frontend Completion | 6 | 9, 11 (AbortController, Settings Save) | Weeks 7-8 |
| **Sprint 5** | Feature Gap + Reliability | 11 | 10, 12-13 (Indicators, Retry, Constants) | Weeks 9-10 |
| **Sprint 6** | Polish + Monitoring | TBD | Monitoring, Analytics, Polish | Weeks 11+ |

---

## Success Metrics

✅ **Quality Gates** (required before merge):
- All tests passing (unit + E2E)
- TypeScript compiles without errors
- No linting violations (ESLint, Black)
- Code review approval
- Acceptance criteria verified

✅ **Velocity**: Target 8-9 points per sprint (adjust after Sprint 1)

✅ **Shipping**: All CRITICAL items complete before v3.3.0 release
