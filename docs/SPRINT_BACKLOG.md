# Sprint Backlog: TickerPulse Checkout Backend

**Last Updated**: 2026-03-05
**Planning Period**: 18 weeks (6 sprints, 3 weeks per sprint)
**Target Velocity**: 8-13 story points per sprint
**Priority Methodology**: Fix critical blocking issues first → High-impact refactoring → Stability → Observability

---

## 📋 Backlog Overview

| Priority | Count | Points | Target Sprint | Impact |
|----------|-------|--------|----------------|--------|
| 🔴 Critical | 5 | 18 | Sprint 1-2 | Blocking runtime errors, security vulnerabilities |
| 🟠 High | 5 | 21 | Sprint 2-4 | Code quality, maintainability, test coverage |
| 🟡 Medium | 3 | 13 | Sprint 4-5 | Database stability, N+1 query fixes |
| 🔵 Low | 2 | 8 | Sprint 5-6 | Observability, performance optimization |
| **TOTAL** | **15** | **60** | **6 sprints** | **Production readiness** |

---

## 🔴 CRITICAL Priority (Sprint 1-2, Weeks 1-4)

Must be fixed before any feature work. These block runtime execution or expose security vulnerabilities.

### TP-C01: Fix Import Path Errors in ai_analytics.py
**User Story**: As a DevOps engineer, I need to fix runtime import errors so the app starts without crashing.

**Acceptance Criteria**:
- [ ] Lines 464-465 corrected to valid Python import syntax
- [ ] Module imports successfully without ImportError
- [ ] All downstream imports in api/analysis.py resolve correctly

**Story Points**: 3 | **Type**: Bug Fix

---

### TP-C02: Add Input Validation to API Period & Limit Parameters
**User Story**: As a security engineer, I need to validate all user-supplied parameters so the API rejects invalid requests.

**Acceptance Criteria**:
- [ ] Query parameter validators added for period (int, 1-252)
- [ ] Query parameter validators added for limit (int, 1-1000)
- [ ] Invalid requests return 400 Bad Request with error message

**Story Points**: 5 | **Type**: Security Fix

---

### TP-C03: Mask API Keys in Logs & Responses
**User Story**: As a security officer, I need to prevent API keys from being logged to avoid credential exposure.

**Acceptance Criteria**:
- [ ] API keys masked in all log output (show only last 4 chars)
- [ ] Config debug logging masks sensitive fields
- [ ] Data provider initialization logs don't expose keys

**Story Points**: 3 | **Type**: Security Fix

---

### TP-C04: Fix Hardcoded SECRET_KEY in config.py
**User Story**: As a DevOps engineer, I need to load SECRET_KEY from environment for unique secrets per deployment.

**Acceptance Criteria**:
- [ ] SECRET_KEY loaded from os.environ.get("SECRET_KEY")
- [ ] Error raised if SECRET_KEY not set in production
- [ ] Test uses test-specific SECRET_KEY

**Story Points**: 2 | **Type**: Security Fix

---

### TP-C05: Add CSRF Token Protection to State-Changing Operations
**User Story**: As a security engineer, I need to enforce CSRF tokens on all POST/PUT/DELETE operations.

**Acceptance Criteria**:
- [ ] CSRF middleware added to FastAPI app
- [ ] All POST/PUT/DELETE endpoints validate CSRF token
- [ ] API returns 403 Forbidden for missing/invalid tokens

**Story Points**: 5 | **Type**: Security Feature

---

## 🟠 HIGH Priority (Sprint 2-4, Weeks 3-9)

### TP-H01: Add Type Hints to Core Functions (Phase 1)
**User Story**: As a backend developer, I need comprehensive type hints so mypy catches type bugs before runtime, reducing production incidents.

**Acceptance Criteria**:
- [ ] All functions in `core/ai_analytics.py`, `core/data_provider.py`, `core/security.py` have return type annotations
- [ ] All function parameters have type hints (no bare `Any`)
- [ ] mypy with strict mode passes on all annotated functions
- [ ] Type coverage report shows ≥95% on core modules

**Definition of Done**:
- Code reviewed and merged
- mypy CI check passes
- Type coverage metrics documented

**Priority**: High because type bugs cause production failures; early detection saves debugging time.

**Complexity**: 8 points based on: 180+ functions to annotate, existing partially-typed codebase, testing type correctness

---

### TP-H02: Refactor Complex Functions (>30 lines)
**User Story**: As a code maintainer, I need to break down complex functions so new team members can debug issues without deep context.

**Acceptance Criteria**:
- [ ] Identify all functions >30 lines in `core/` (target: 8-12 functions)
- [ ] Refactor into smaller, single-purpose functions (<20 lines each)
- [ ] Unit test coverage increases from 42% to ≥70% on refactored modules
- [ ] All functions have docstrings explaining inputs/outputs/exceptions

**Definition of Done**:
- Code reviewed and merged
- Tests passing (100% of old tests still pass)
- Complexity metrics improved

**Priority**: High because complex functions are debugging bottlenecks and onboarding friction.

**Complexity**: 8 points based on: 500+ LOC to refactor, requires careful test preservation, risk of introducing regressions

---

### TP-H03: Consolidate Hardcoded Constants into Config
**User Story**: As a data scientist, I need indicator parameters (RSI period=14, BB std=2) in centralized config so I can tune performance without code changes.

**Acceptance Criteria**:
- [ ] Create `config/indicators.py` with all hardcoded constants (RSI, Bollinger Bands, MACD, Stochastic)
- [ ] Load from environment: `INDICATOR_RSI_PERIOD` (default 14), `INDICATOR_BB_STD` (default 2)
- [ ] All 8+ indicator functions read from config, not hardcoded values
- [ ] Integration test verifies config changes affect indicator output

**Definition of Done**:
- Code reviewed and merged
- Tests passing
- Config documentation with all parameters listed

**Priority**: High because current hardcoded values prevent A/B testing and parameter tuning.

**Complexity**: 5 points based on: locating all constants (40-50 values), refactoring 8 functions, minimal risk

---

### TP-H04: Add Structured Logging & Error Context
**User Story**: As a DevOps engineer, I need structured JSON logs with request IDs and stack traces so I can trace production errors in ELK without SSH'ing servers.

**Acceptance Criteria**:
- [ ] Replace all `print()` with `logger.info()` / `logger.error()` (target: 50+ locations)
- [ ] All error logs include: request_id, user_id, operation, error_code, stack trace
- [ ] Log output is JSON (parseable by ELK/Splunk)
- [ ] Integration test verifies error log contains all required fields

**Definition of Done**:
- Code reviewed and merged
- Tests passing
- Logging documentation with example log format

**Priority**: High because production errors are currently untrackable; structured logs enable rapid incident response.

**Complexity**: 5 points based on: systematic logger replacement, structlog integration (pre-configured), low risk

---

### TP-H05: Add Unit Tests for Agent Framework & Data Providers
**User Story**: As a test engineer, I need comprehensive unit tests for agent initialization and fallback chains so providers that fail don't cascade silently.

**Acceptance Criteria**:
- [ ] 100% test coverage on `AgentPool` initialization and provider fallback logic
- [ ] Test cases cover: all providers available, 1 provider fails, all providers fail, network timeout
- [ ] Mock external API calls (avoid test flakiness)
- [ ] Test suite runs in <5s (no network I/O)

**Definition of Done**:
- Code reviewed and merged
- Tests passing (100% coverage verified)
- CI enforces coverage >95% on agent module

**Priority**: High because silent provider failures cause incomplete data in production; tests validate resilience.

**Complexity**: 8 points based on: mocking 4 external providers, testing 6 fallback scenarios, async/await patterns

---

## 🟡 MEDIUM Priority (Sprint 4-5, Weeks 7-10)

### TP-M01: Fix N+1 Query Patterns in Batch Rating Calculation
**User Story**: As a database administrator, I need to eliminate N+1 queries in batch rating so 100-ticker requests complete in <2s instead of 30s.

**Acceptance Criteria**:
- [ ] Profile batch rating calculation: capture baseline query count and latency
- [ ] Refactor to use single `JOIN` query instead of loop + per-ticker queries (target: 100 queries → 2)
- [ ] Load test: 100-ticker batch completes in <2s at p95
- [ ] DB connection count stays <10 (no connection exhaustion)

**Definition of Done**:
- Code reviewed and merged
- Performance test passing (2s SLA met)
- Query plan documented

**Priority**: Medium because batch requests are common but N+1 patterns degrade gracefully; fixing improves user experience.

**Complexity**: 5 points based on: identifying N+1 in batch_calculate_ratings, 1 SQL refactor, performance test

---

### TP-M02: Implement Database Connection Pooling
**User Story**: As an SRE, I need connection pooling so peak load (100 concurrent requests) doesn't exhaust SQLite connections.

**Acceptance Criteria**:
- [ ] Configure SQLAlchemy connection pool: pool_size=10, max_overflow=20
- [ ] Load test: 100 concurrent requests with <5 DB connection errors
- [ ] Monitor: log connection pool usage (utilization %, wait time)
- [ ] Integration test verifies pool doesn't leak connections

**Definition of Done**:
- Code reviewed and merged
- Load test passing
- Connection pool metrics exported to monitoring

**Priority**: Medium because connection exhaustion only appears at scale; current load isn't hitting it, but will during growth.

**Complexity**: 5 points based on: pool configuration, connection leak detection, minimal code changes

---

### TP-M03: Implement Circuit Breaker for External API Calls
**User Story**: As a reliability engineer, I need circuit breaker protection so a failing data provider (60sec timeout) doesn't block all requests for 60 seconds.

**Acceptance Criteria**:
- [ ] Circuit breaker state machine: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)
- [ ] Trip when >5 failures in 60s window, recover after 30s silence
- [ ] Request during OPEN state fails fast (<100ms) with fallback provider
- [ ] Log all state transitions and recovery events

**Definition of Done**:
- Code reviewed and merged
- Tests passing (all 3 state transitions tested)
- Integration test: simulated provider failure recovers correctly

**Priority**: Medium because provider failures are rare but impact is high; circuit breaker prevents cascades during incidents.

**Complexity**: 8 points based on: state machine implementation, testing 3 states + transitions, configurable thresholds

---

## 🔵 LOW Priority (Sprint 5-6, Weeks 11+)

### TP-L01: Implement Caching Layer for Indicator Calculations
**User Story**: As a performance engineer, I need to cache indicator calculations (RSI, Bollinger Bands) for 5 minutes so repeated requests for same ticker don't recalculate.

**Acceptance Criteria**:
- [ ] Add Redis cache layer (fall back to in-memory if Redis unavailable)
- [ ] Cache key: `indicator:{ticker}:{period}:{type}`, TTL=300s
- [ ] Cache hit rate target: ≥60% during trading hours (8am-4pm EST)
- [ ] Integration test verifies cache hit/miss behavior

**Definition of Done**:
- Code reviewed and merged
- Tests passing
- Cache hit rate metrics exported

**Priority**: Low because caching is a performance optimization, not a correctness fix. Deferred until after stability is proven.

**Complexity**: 5 points based on: Redis integration, cache key design, TTL logic, no external vendor lock-in needed

---

### TP-L02: Add Prometheus Metrics & Observability Dashboard
**User Story**: As an SRE, I need Prometheus metrics (request latency, DB query time, provider call duration) so I can detect performance regressions before users report them.

**Acceptance Criteria**:
- [ ] Export 3 core metrics: `http_request_duration_seconds` (histogram), `db_query_duration_seconds`, `data_provider_call_duration_seconds`
- [ ] Prometheus scrape endpoint: `GET /metrics`
- [ ] Grafana dashboard displays: latency p50/p95/p99, error rate, provider fallback count
- [ ] Alert rule: trigger if p99 latency > 5s

**Definition of Done**:
- Code reviewed and merged
- Tests passing
- Grafana dashboard deployed and verified

**Priority**: Low because metrics are observability tooling, not functionality. Deferred until core features are stable and measurable.

**Complexity**: 5 points based on: Prometheus client integration, metric definition, minimal code changes

---

## 📊 Sprint Delivery Schedule

| Sprint | Weeks | Velocity | Focus | Tasks |
|--------|-------|----------|-------|-------|
| 1 | 1-3 | 13 pts | Critical runtime fixes | TP-C01-C04 |
| 2 | 4-6 | 16 pts | Security + type hints | TP-C05, TP-H01, TP-H04 |
| 3 | 7-9 | 13 pts | Refactoring & config | TP-H02, TP-H03, TP-H05 |
| 4 | 10-12 | 10 pts | Testing & N+1 fixes | TP-H05, TP-M01 |
| 5 | 13-15 | 13 pts | Infrastructure | TP-M02, TP-M03, TP-L01 |
| 6+ | 16-18 | 5 pts | Observability | TP-L02 |

**Total**: 60 points across 15 tasks over 6 sprints (18 weeks)

---

## ✅ Success Criteria

- [ ] All 15 tasks completed and merged
- [ ] Code review approved for every task
- [ ] Test coverage > 80% on critical paths
- [ ] Zero critical/high security findings
- [ ] Type hints: 95%+ coverage
- [ ] All tests passing (unit + integration)
- [ ] Load test: p99 latency < 5s at 100 concurrent requests
