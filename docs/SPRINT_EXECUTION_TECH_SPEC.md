# Sprint Execution Technical Design Spec

**Document**: Implementation strategy for 15 backlog items (60 story points, 18 weeks)
**Audience**: Dev team, tech lead, QA
**Last Updated**: 2026-03-05
**Version**: 1.0

---

## 📋 Implementation Overview

### Delivery Model: Sequential Priority Batching

```
┌─────────────────────────────────────────────────────────────┐
│ STRATEGY: Fix critical issues first → High refactoring →    │
│           Database optimization → Observability               │
│                                                             │
│ PARALLEL WORK: While refactoring runs (Sprints 3-5),       │
│                testing & docs can be developed              │
└─────────────────────────────────────────────────────────────┘
```

### Why This Order?

1. **Sprints 1-2 (Critical fixes)**: Runtime errors block everything. Must fix before refactoring.
2. **Sprint 3-4 (Refactoring + Testing)**: High-quality code with tests. Safer to refactor at 100% test coverage.
3. **Sprint 5 (Database)**: Once code is stable, optimize queries & connections.
4. **Sprint 6+ (Observability)**: Monitor stable system to understand where to optimize next.

---

## 🛠️ Files & Modules Affected

### Core Changes (Existing Files)

| File | Sprint | Tasks | Changes |
|------|--------|-------|---------|
| `backend/core/ai_analytics.py` | 1 | TP-C01, TP-H01, TP-H02 | Fix imports, add type hints, refactor functions |
| `backend/core/config.py` | 1-2 | TP-C04, TP-H03 | SECRET_KEY from env, consolidate constants |
| `backend/core/data_providers.py` | 2-3 | TP-H01, TP-H04, TP-H05, TP-M03 | Type hints, logging, tests, circuit breaker |
| `backend/core/database.py` | 5 | TP-M02 | Connection pooling configuration |
| `backend/api/analysis.py` | 1, 4 | TP-C02, TP-M01 | Validate params, optimize N+1 queries |
| `backend/api/ratings.py` | 1-2 | TP-C02, TP-C03, TP-H04 | Validate params, mask keys, structured logging |
| `backend/api/indicators.py` | 1-2 | TP-C02, TP-H01 | Validate params, add type hints |
| `backend/main.py` | 2, 6 | TP-C05, TP-L02 | CSRF middleware, Prometheus metrics |

### New Files (Modules)

| File | Sprint | Purpose |
|------|--------|---------|
| `backend/core/security.py` | 1 | API key masking utility |
| `backend/core/resilience.py` | 5 | Circuit breaker implementation |
| `backend/core/metrics.py` | 6 | Prometheus metrics definitions |
| `backend/tests/test_critical_fixes_verification.py` | 1-2 | Unit tests for critical fixes |
| `backend/tests/test_agent_framework.py` | 3-4 | Agent initialization tests |
| `backend/tests/test_data_providers.py` | 3-4 | Data provider chain tests |
| `grafana/dashboards/backend-metrics.json` | 6 | Observability dashboard |

### Configuration Changes

| File | Sprint | Purpose |
|------|--------|---------|
| `pyproject.toml` | 2 | mypy strict mode configuration |
| `.pre-commit-config.yaml` | 2 | Add mypy to pre-commit hooks |
| `docker-compose.test.yml` | 5 | Add Redis for caching (optional) |

---

## 🔄 Detailed Implementation Approach

### Sprint 1: Critical Fixes (Weeks 1-3)

#### TP-C01: Fix Import Path Errors
```python
# backend/core/ai_analytics.py (lines 464-465)
# BEFORE (BROKEN):
from backend.ratings import calculate_ratings  # Wrong path

# AFTER (FIXED):
from backend.api.ratings import calculate_ratings  # Correct path
```
- **Owner**: Backend dev
- **Dependencies**: None
- **Testing**: Run `python -c "from backend.core.ai_analytics import *"` and verify no errors
- **Files modified**: `ai_analytics.py` (1 file)
- **Estimated time**: 1 day

#### TP-C02: Validate API Parameters
```python
# backend/api/analysis.py
from fastapi import Query

@router.get("/ratings")
async def get_ratings(
    symbol: str,
    period: int = Query(14, ge=1, le=252),  # Add validation
    limit: int = Query(100, ge=1, le=1000),
):
    # Validation automatic via Pydantic
```
- **Owner**: Backend dev
- **Dependencies**: None (no external APIs)
- **Testing**: Unit tests for boundary cases (0, -1, 999999, "abc")
- **Files modified**: `analysis.py`, `ratings.py`, `indicators.py` (3 files)
- **Estimated time**: 3 days

#### TP-C03: Mask API Keys
```python
# NEW FILE: backend/core/security.py

def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive strings, showing only last N characters."""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]

# Usage:
masked_key = mask_sensitive_value(api_key)  # Returns: "...abcd"
logger.info(f"Using API key: {masked_key}")
```
- **Owner**: Backend dev
- **Dependencies**: None
- **Testing**: Unit tests for various string lengths
- **Files modified**: `config.py`, `data_providers.py` (2 files), NEW: `security.py`
- **Estimated time**: 2 days

#### TP-C04: Fix SECRET_KEY
```python
# backend/core/config.py

import os

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if os.environ.get("ENV") == "production":
        raise ValueError("SECRET_KEY environment variable not set in production")
    SECRET_KEY = "dev-secret-key-change-in-production"
```
- **Owner**: Backend dev
- **Dependencies**: None
- **Testing**: Unit test verifies error in production mode without env var
- **Files modified**: `config.py` (1 file)
- **Estimated time**: 1 day

#### TP-C05: Add CSRF Tokens (partial in Sprint 1, complete in Sprint 2)
- **Owner**: Backend + Frontend dev
- **Dependencies**: Know before Sprint 2
- **Estimated time**: 5 days (2 days Sprint 1, 3 days Sprint 2)

---

### Sprint 2: Security + Refactoring Start (Weeks 4-6)

#### TP-C05: Complete CSRF Implementation
```python
# backend/main.py
from fastapi_csrf_protect import CsrfProtect

app.add_middleware(CsrfProtect)

# backend/api/ratings.py (example endpoint)
@router.post("/ratings")
@app.csrf_protect
async def create_rating(data: RatingData):
    # CSRF token automatically validated
```
- **Testing**: Integration tests verify 403 on missing token
- **Files modified**: `main.py`, all state-changing endpoints (5+ files)
- **Estimated time**: 3 days (spread across Sprint 2)

#### TP-H01: Add Type Hints (Phase 1)
```python
# backend/core/ai_analytics.py (example)

from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class RatingResult:
    symbol: str
    score: float
    indicators: Dict[str, float]

async def calculate_ai_rating(symbol: str, period: int = 14) -> RatingResult:
    """Calculate AI rating for a stock symbol."""
    # All parameters and return type annotated
    ...
```
- **Owner**: Backend dev
- **Dependencies**: None
- **Testing**: Run `mypy --strict backend/core/` and verify 0 errors
- **Files modified**: `ai_analytics.py`, `config.py`, `data_providers.py` (3 files)
- **Estimated time**: 3 days

#### TP-H04: Logging & Error Context
```python
# backend/core/database.py (example)
import structlog

logger = structlog.get_logger(__name__)

async def get_stock_data(symbol: str) -> Optional[Dict]:
    try:
        result = await db.fetch(...)
        logger.debug("fetch_success", symbol=symbol, rows=len(result))
        return result
    except Exception as e:
        logger.exception("fetch_failed", symbol=symbol, error=str(e))
        raise
```
- **Owner**: Backend dev
- **Dependencies**: TP-C01-C04 complete
- **Testing**: Unit tests verify error logs include context
- **Files modified**: All core modules (5+ files)
- **Estimated time**: 3 days

---

### Sprint 3-4: Deep Refactoring (Weeks 7-12)

#### TP-H02: Refactor Complex Functions
```python
# BEFORE (175 lines):
async def calculate_ai_rating(symbol: str) -> float:
    # Fetch indicators
    # Calculate scores
    # Apply weights
    # Log results
    # Format output
    # ... 175 lines of tangled logic

# AFTER (3 focused functions):
async def _fetch_indicators(symbol: str) -> Dict[str, float]:
    """Fetch RSI, MACD, Moving Average. ~40 lines."""

async def _calculate_scores(indicators: Dict) -> Dict[str, float]:
    """Score each indicator. ~35 lines."""

async def _apply_weights(scores: Dict) -> float:
    """Weight scores into final rating. ~30 lines."""
```
- **Owner**: Backend dev
- **Dependencies**: TP-H01 (type hints first)
- **Testing**: Unit tests for each sub-function + integration test
- **Files modified**: `ai_analytics.py`, `ratings.py` (2 files)
- **Estimated time**: 5 days

#### TP-H03: Consolidate Config
```python
# NEW: backend/core/config.py additions

from dataclasses import dataclass
from typing import Dict

@dataclass
class IndicatorDefaults:
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    sma_50_period: int = 50
    sma_200_period: int = 200

@dataclass
class RatingTiers:
    strong_buy: int = 80
    buy: int = 65
    hold: int = 50
    sell: int = 35
```
- **Owner**: Backend dev
- **Dependencies**: TP-C03 (constants already identified)
- **Testing**: Unit tests verify all imports use config
- **Files modified**: 8+ files (every indicator function)
- **Estimated time**: 3 days

#### TP-H05: Agent Framework Tests
```python
# NEW FILE: backend/tests/test_agent_framework.py

async def test_agent_initialization_success():
    """Agent initializes with valid config."""
    agent = await AgentFramework.initialize(config=valid_config)
    assert agent is not None

async def test_agent_fallback_on_missing_provider():
    """Agent uses secondary provider if primary fails."""
    # Mock primary provider to fail
    agent = await AgentFramework.initialize(config=config)
    result = await agent.analyze(symbol)
    assert result.provider == "secondary"

async def test_data_provider_chain():
    """Providers tried in order: Alpha Vantage → IEX → Reddit."""
    # Mock each provider with different failures
```
- **Owner**: QA/Backend dev
- **Dependencies**: None (mocking used)
- **Testing**: All tests passing, coverage > 80%
- **Files**: NEW: `test_agent_framework.py`, `test_data_providers.py`
- **Estimated time**: 4 days

---

### Sprint 5: Database Optimization (Weeks 13-15)

#### TP-M01: Fix N+1 Queries
```python
# BEFORE (N+1 queries):
stocks = ["AAPL", "MSFT", "GOOGL"]
for symbol in stocks:
    rating = await get_rating(symbol)  # N queries

# AFTER (optimized):
ratings = await get_ratings_batch(symbols=stocks)  # 1-2 queries
# Uses JOIN, fetches all data at once
```
- **Owner**: Backend dev
- **Dependencies**: TP-H02 (refactored functions easier to optimize)
- **Testing**: Integration test verifies query count < 5
- **Files modified**: `analysis.py`, `database.py` (2 files)
- **Estimated time**: 3 days

#### TP-M02: Connection Pooling
```python
# backend/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,      # Min connections
    max_overflow=15,  # Max additional connections
    pool_timeout=30,  # Fail fast
)
```
- **Owner**: Infrastructure dev
- **Dependencies**: None (isolated change)
- **Testing**: Load test with 50 concurrent requests
- **Files modified**: `database.py` (1 file)
- **Estimated time**: 2 days

#### TP-M03: Circuit Breaker
```python
# NEW FILE: backend/core/resilience.py

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.state = "CLOSED"  # Normal operation
        self.failure_count = 0
        self.timeout = timeout

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            raise CircuitBreakerOpen("Circuit is open")
        try:
            result = await func(*args, **kwargs)
            self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise

# Usage in data providers:
circuit_breaker = CircuitBreaker()
try:
    data = await circuit_breaker.call(alpha_vantage.get_price, symbol)
except CircuitBreakerOpen:
    data = await fallback_provider.get_price(symbol)
```
- **Owner**: Backend dev
- **Dependencies**: None (new module)
- **Testing**: Unit tests for CLOSED→OPEN→HALF_OPEN transitions
- **Files**: NEW: `resilience.py`, modify `data_providers.py` (2 files)
- **Estimated time**: 4 days

---

### Sprint 6+: Observability (Weeks 16-18)

#### TP-L02: Prometheus Metrics
```python
# NEW FILE: backend/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge

request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint"]
)

request_latency = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

cache_hits = Counter(
    "cache_hits_total",
    "Cache hit count"
)

# backend/main.py
from prometheus_client import make_asgi_app
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```
- **Owner**: Infrastructure dev
- **Dependencies**: None (isolated change)
- **Testing**: Verify metrics exposed on `/metrics`
- **Files**: NEW: `metrics.py`, NEW: `grafana/dashboards/backend-metrics.json`
- **Estimated time**: 3 days

---

## 🧪 Testing Strategy Across Sprints

### Unit Tests (Sprint 1+)
- Each task includes unit test file
- Tests cover happy path, error cases, edge cases
- Run tests before every commit: `pytest backend/tests/ -v`

### Integration Tests (Sprint 2+)
- Tests verify end-to-end behavior (e.g., API → DB → Response)
- Run before merge: `pytest backend/tests/ -v -m integration`

### Load Tests (Sprint 5-6)
- Verify performance under load (100 concurrent requests)
- Verify connection pooling doesn't exhaust connections
- Tool: `locust` or `k6`

### Pre-Commit Hooks
```bash
# .pre-commit-config.yaml additions
- repo: local
  hooks:
    - id: mypy
      name: mypy type checking
      entry: mypy backend/ --strict
      language: system
      types: [python]

    - id: pytest
      name: pytest unit tests
      entry: pytest backend/tests/ -v
      language: system
      stages: [commit]
```

---

## 📅 Timeline & Milestones

| Sprint | Weeks | Velocity | Milestone |
|--------|-------|----------|-----------|
| 1 | 1-3 | 13 pts | Critical fixes merged |
| 2 | 4-6 | 11 pts | CSRF + Type hints complete |
| 3 | 7-9 | 13 pts | Refactoring done, 80%+ test coverage |
| 4 | 10-12 | 10 pts | Agent tests passing, N+1 fixed |
| 5 | 13-15 | 13 pts | Connection pooling + Circuit breaker |
| 6+ | 16-18 | 5 pts | Metrics + Dashboards |

**Total**: 60 points, 18 weeks, 1 dev @100% or 2 devs @50% = 9 weeks

---

## 🚦 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Refactoring breaks functionality | Medium | High | 80%+ test coverage first, incremental changes |
| N+1 query optimization has edge cases | Medium | Medium | Thorough benchmarking before/after |
| Circuit breaker misconfigured | Low | High | Extensive testing of state transitions |
| Type hints reveal existing bugs | Medium | Low | Address bugs as found, prioritize critical |
| Load test fails connection pooling | Low | High | Start with conservative pool size (5), increase gradually |

---

## ✅ Definition of Done (Per Task)

Every task completion requires:

- [ ] Code written, type-safe, follows conventions
- [ ] Unit tests passing (happy + error + edge cases)
- [ ] Integration tests passing (if applicable)
- [ ] Code review approved by tech lead
- [ ] Documentation updated (if spec changed)
- [ ] Pre-commit hooks pass (mypy, pytest, linting)
- [ ] Commit message references task ID (e.g., "fix: TP-C01 Fix import paths")

---

## 📞 Escalation Path

- **Blocked on dependencies**: File as new task in next sprint
- **New requirements discovered**: Update docs, re-estimate task
- **Performance regression**: Rollback, investigate root cause, re-plan
- **Major blocker**: Escalate to tech lead immediately

---

**Ready to execute**. Backlog prioritized, acceptance criteria defined, risks identified. First sprint can start immediately with TP-C01 through TP-C04.