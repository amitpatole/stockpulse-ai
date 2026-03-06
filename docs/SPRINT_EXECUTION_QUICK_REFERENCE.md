# Sprint Execution Quick Reference

**Duration**: 18 weeks (6 sprints, 60 story points)
**Team**: 1 dev @100% or 2 devs @50%
**Strategy**: Fix critical bugs → Refactor → Optimize → Monitor

---

## 🎯 Approach

Sequential priority batching ensures runtime stability before refactoring. Critical fixes unblock all other work. Once code is type-safe with 80%+ test coverage, database optimization is safer. Finally, instrument the stable system for insights.

```
Sprint 1-2  →  Critical fixes (5 items, 18 pts)
Sprint 3-4  →  Refactoring + tests (5 items, 21 pts)
Sprint 5    →  Database optimization (3 items, 13 pts)
Sprint 6+   →  Observability (2 items, 8 pts)
```

---

## 📁 Files to Modify/Create

### Core Modules (Modify)
- `backend/core/ai_analytics.py` - Fix imports, add type hints (Sprints 1-3)
- `backend/core/config.py` - Consolidate constants, SECRET_KEY from env (Sprints 1-2)
- `backend/core/data_providers.py` - Type hints, logging, circuit breaker (Sprints 2-5)
- `backend/core/database.py` - Connection pooling (Sprint 5)
- `backend/api/analysis.py`, `ratings.py`, `indicators.py` - Validate params, optimize queries (Sprints 1, 4-5)
- `backend/main.py` - CSRF middleware, Prometheus metrics (Sprints 2, 6)

### New Files (Create)
- `backend/core/security.py` - API key masking utility (Sprint 1)
- `backend/core/resilience.py` - Circuit breaker implementation (Sprint 5)
- `backend/core/metrics.py` - Prometheus metrics definitions (Sprint 6)
- `backend/tests/test_critical_fixes_verification.py` - Unit tests (Sprints 1-2)
- `backend/tests/test_agent_framework.py` - Agent initialization tests (Sprints 3-4)
- `backend/tests/test_data_providers.py` - Provider chain tests (Sprints 3-4)
- `grafana/dashboards/backend-metrics.json` - Observability dashboard (Sprint 6)

### Config Changes
- `pyproject.toml` - Add mypy strict mode (Sprint 2)
- `.pre-commit-config.yaml` - Add mypy + pytest hooks (Sprint 2)

---

## 📊 Data Model Changes

**No new database tables required.** All changes work within existing SQLite schema:
- Add index on `stocks.symbol` if missing (query optimization)
- Add index on `analysis.created_at` for time-range queries
- Verify foreign key constraints enabled in database.py

---

## 🔗 API Changes

**No new endpoints.** Modifications to existing endpoints:

```python
GET /api/analysis/ratings?symbol=AAPL&period=14&limit=100
├─ Add validation: period (1-252), limit (1-1000)
├─ Add CSRF token check (POST requests)
└─ Mask API keys in error responses

POST /api/ratings
├─ Require CSRF token from client
└─ Return 403 if token missing/invalid
```

---

## 🎨 Frontend Changes

Minimal changes required:
- Add CSRF token fetch on app startup: `GET /api/csrf-token`
- Include token in POST/PUT/DELETE request headers: `X-CSRF-Token`
- No new components, routes, or state management needed

---

## 🧪 Testing Strategy

| Phase | Test Type | Coverage | Tools |
|-------|-----------|----------|-------|
| Sprint 1-2 | Unit tests | All business logic | pytest + mock |
| Sprint 3-4 | Integration tests | End-to-end flows | pytest + fixtures |
| Sprint 5-6 | Load tests | Concurrency + pooling | locust or k6 |

**Pre-commit enforcement**:
```bash
pytest backend/tests/ -v            # All tests pass
mypy backend/ --strict              # No type errors
black --check backend/              # Code format
```

---

## 🚀 Definition of Done (Per Task)

- [ ] Code written with full type hints (no `any`)
- [ ] Unit tests: happy path + error cases + edge cases
- [ ] All tests passing + >80% coverage on modified files
- [ ] Code review approved by tech lead
- [ ] Pre-commit hooks passing
- [ ] Commit references task ID (e.g., "fix: TP-C01")

---

## 📅 Key Milestones

| Week | Sprint | Deliverable | Velocity |
|------|--------|-------------|----------|
| 1-3 | 1 | Critical fixes merged | 13 pts |
| 4-6 | 2 | Security + type hints | 11 pts |
| 7-9 | 3 | Refactoring + tests | 13 pts |
| 10-12 | 4 | Agent tests complete | 10 pts |
| 13-15 | 5 | Database optimized | 13 pts |
| 16-18 | 6 | Metrics + dashboards | 5 pts |

**Total**: 60 points in 18 weeks

---

**For detailed implementation steps per task, see** `SPRINT_EXECUTION_TECH_SPEC.md`
**For full backlog with acceptance criteria, see** `SPRINT_BACKLOG.md`
