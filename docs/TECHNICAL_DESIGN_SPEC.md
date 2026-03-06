# Technical Design Spec: TickerPulse Sprint Execution

**Document**: Architecture & implementation guide for 15 backlog items (60 points, 18 weeks)
**Audience**: Dev team, QA, technical leads
**Last Updated**: 2026-03-05

---

## 1. Approach: Sequential Priority + Parallel Testing

**Strategy**: Fix blocking issues first → refactor with tests → optimize infrastructure → observe

```
Phase 1 (Weeks 1-4):   Critical fixes (5 items, 18 pts)
                       ↓ Unblocks everything
Phase 2 (Weeks 5-9):   Refactoring + testing (5 items, 21 pts)
                       ↓ Only when code is stable
Phase 3 (Weeks 10-18): Optimization + observability (5 items, 21 pts)
```

**Rationale**: Runtime errors block execution. Refactoring is safer at 100% test coverage. Optimization requires stable baseline.

---

## 2. Files to Modify/Create

### Core Backend (Modified)
- `backend/core/ai_analytics.py` - Import fixes (C01), type hints (H01), refactoring (H02)
- `backend/core/config.py` - SECRET_KEY from env (C04), indicator constants (H03)
- `backend/core/data_providers.py` - Type hints (H01), structured logging (H04), tests (H05), circuit breaker (M03)
- `backend/core/database.py` - Connection pooling (M02)
- `backend/api/analysis.py` - Parameter validation (C02), N+1 optimization (M01)
- `backend/api/ratings.py` - Validation (C02), key masking (C03), logging (H04)
- `backend/api/indicators.py` - Validation (C02), type hints (H01)
- `backend/main.py` - CSRF middleware (C05), Prometheus metrics (L02)

### New Modules
- `backend/core/security.py` - API key masking utility
- `backend/core/resilience.py` - Circuit breaker state machine
- `backend/core/metrics.py` - Prometheus metric definitions
- `backend/tests/test_critical_fixes.py` - Verification for C01-C05
- `backend/tests/test_agent_framework.py` - Provider fallback coverage (H05)
- `grafana/dashboards/backend-metrics.json` - Observability dashboard

---

## 3. Data Model Changes

**No schema changes required.** All improvements are at application layer:

- **Config tables** (new): Load indicator parameters from environment, not hardcoded
  - RSI period (default 14) → `INDICATOR_RSI_PERIOD` env
  - Bollinger Bands std (default 2) → `INDICATOR_BB_STD` env
  - Add 40+ more tunable constants to `backend/config/indicators.py`

- **Logging** (no schema): Structured JSON logs with request_id, user_id, operation, error_code
  - Use `structlog` library (already vendored)
  - Replace 50+ print() calls with logger.info()/error()

- **Caching** (optional): Redis connection pool for indicator cache (Sprint 5)
  - Key format: `indicator:{ticker}:{period}:{type}` TTL=300s
  - Fallback to in-memory if Redis unavailable

---

## 4. API Changes

All endpoints return `{data, meta, errors}` structure (existing standard).

### New Validation Layer
- **GET /api/analysis/ratings** - Query params: `period` (int, 1-252), `limit` (int, 1-100) with 400 Bad Request on invalid
- **GET /api/ratings** - Same validation + API key masking in responses
- **GET /api/indicators** - Period/limit validation

### New Endpoints
- **POST /api/csrf-token** - Return CSRF token for form submissions (existing pattern)
- **GET /metrics** - Prometheus metrics export (new, no auth required for internal scrape)

### Error Responses
- 400 Bad Request: Invalid period/limit parameters
- 403 Forbidden: Missing/invalid CSRF token on state-changing ops
- 500 Internal Error: Includes request_id for log correlation

---

## 5. Frontend Changes

**No frontend code changes required** for this sprint.

**Why**: All 15 tasks are backend-focused (imports, validation, security, type hints, tests, observability).

**Future impact**: Once backend metrics (L02) export, frontend can display:
- API latency dashboard (p50/p95/p99)
- Provider fallback rates (circuit breaker stats)
- Data freshness indicators

---

## 6. Testing Strategy

### Unit Tests (70% of effort)
- **Critical fixes** (C01-C05): Import, validation, CSRF, key masking
  - File: `test_critical_fixes.py` (30+ tests, 2s runtime)
  - Coverage: Happy path + error cases + edge cases

- **Type hints** (H01): mypy strict mode on core modules
  - Pre-commit hook: `mypy backend/core --strict`
  - CI enforces 95%+ type coverage

- **Agent framework** (H05): Provider initialization, fallback chain, all failure modes
  - File: `test_agent_framework.py` (25+ tests, <5s runtime)
  - Mock all external APIs (avoid flakiness)

### Integration Tests (20% of effort)
- **N+1 queries** (M01): Load test batch_calculate_ratings with 100 tickers, verify <2s p95
- **Connection pooling** (M02): 100 concurrent requests, <5 connection errors
- **Circuit breaker** (M03): Inject provider failure, verify fast fallback recovery

### Definition of Done
```
✅ All unit tests pass
✅ mypy strict mode: 0 errors
✅ Code coverage ≥80% on critical paths
✅ Integration tests < 5s runtime
✅ Load tests: p99 latency < 5s at 100 RPS
✅ Code review approved
✅ No new security findings
```

---

## Summary: Sprint Readiness Checklist

- [ ] All 15 tasks have detailed acceptance criteria (SPRINT_BACKLOG.md)
- [ ] File impact matrix documented (section 2 above)
- [ ] No database migration required
- [ ] API response format consistent with existing standard
- [ ] Tests written before implementation (TDD)
- [ ] mypy + ESLint pre-commit hooks enforced
- [ ] Docs + code commit together

**Target**: All critical (C01-C05) + high (H01-H05) complete by week 9. Ready for production deployment.
