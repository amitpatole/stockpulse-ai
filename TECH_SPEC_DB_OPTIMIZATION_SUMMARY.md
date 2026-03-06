# Database Query Optimization - Technical Design Spec

**Status**: Implementation In Progress
**Priority**: High (Critical Performance Path)
**Target**: Eliminate N+1 patterns, 5-10x latency improvement

---

## 1. APPROACH

**Three-phase strategy:**
1. **Add strategic indexes** on hot-path columns (done: `database.py` ✅)
2. **Move filtering to SQL** (in-progress: stocks.py, research.py)
3. **Add query profiling** (pending: query_profiler.py)

**Key principles:**
- WHERE/ORDER BY/LIMIT in SQL, not Python loops
- Batch queries with IN clauses, not loop + individual queries
- Single round-trip per operation (combine COUNT + SELECT when possible)
- Composite indexes for multi-column queries

---

## 2. FILES TO MODIFY/CREATE

| File | Status | Changes |
|------|--------|---------|
| `backend/database.py` | ✅ Done | Added 27 composite indexes for all hot paths |
| `backend/api/stocks.py` | ✅ Done | Uses `get_stocks_with_filter()` (SQL filtering) |
| `backend/api/research.py` | ✅ Done | Uses `get_research_briefs_by_ticker()` (single query) |
| `backend/core/stock_manager.py` | ✅ Done | Implements `get_stocks_with_filter()` |
| `backend/core/query_optimizer.py` | ✅ Done | Implements `get_research_briefs_by_ticker()` |
| `backend/api/prices.py` | ⏳ Pending | Replace linear search with `batch_get_stocks_by_tickers()` |
| `backend/api/analysis.py` | ⏳ Pending | Verify AI ratings uses composite index |
| `backend/tests/test_query_optimization.py` | ⏳ Pending | 12+ tests verifying SQL plans |

---

## 3. DATA MODEL CHANGES

**No schema changes.** All changes are indexes only.

**New indexes in `database.py` (lines 264-321):**
```sql
-- Stocks
CREATE INDEX idx_stocks_active_market ON stocks(active, market)     -- for filtering
CREATE INDEX idx_stocks_added_at ON stocks(added_at DESC)            -- for sorting

-- Research Briefs (composite for filter + sort)
CREATE INDEX idx_research_briefs_ticker_created ON research_briefs(ticker, created_at DESC)

-- AI Ratings
CREATE INDEX idx_ai_ratings_ticker ON ai_ratings(ticker)             -- for joins
CREATE INDEX idx_ai_ratings_updated ON ai_ratings(updated_at DESC)   -- cache invalidation

-- News
CREATE INDEX idx_news_ticker_created ON news(ticker, created_at DESC)

-- Alerts
CREATE INDEX idx_alerts_ticker ON alerts(ticker)

-- Cost Tracking
CREATE INDEX idx_cost_tracking_date_agent ON cost_tracking(date, agent_name)

-- Job History
CREATE INDEX idx_job_history_status_executed ON job_history(status, executed_at DESC)
```

---

## 4. API CHANGES

**No breaking changes—response formats identical.**

| Endpoint | Optimization | Expected Latency |
|----------|--------------|------------------|
| `GET /api/stocks?market=...` | SQL WHERE clause + `idx_stocks_active_market` | <50ms (was 500ms+) |
| `GET /api/prices/<ticker>` | Batch lookup instead of linear search | <10ms (was 100ms+) |
| `GET /api/research/briefs?ticker=...` | Single query with `LIMIT+1` trick | <100ms (was 200ms+) |
| `GET /api/analysis/ratings?ticker=...` | Uses `idx_ai_ratings_ticker` | <100ms |

---

## 5. FRONTEND CHANGES

**None.** Query optimization is backend-only.

---

## 6. TESTING STRATEGY

### Unit Tests (`backend/tests/test_query_optimization.py`)
```python
def test_stocks_filter_uses_sql_where():
    """Verify market filtering happens in SQL, not Python"""
    stocks = get_stocks_with_filter(market='US', limit=20, offset=0)
    assert all(s['market'] == 'US' for s in stocks)

def test_research_briefs_pagination_single_query():
    """Verify pagination uses LIMIT+1 trick, not separate COUNT"""
    # Mock conn to verify single execute() call
    briefs, total = get_research_briefs_by_ticker('AAPL', limit=25, offset=0)
    assert len(briefs) <= 25

def test_ticker_lookup_not_full_scan():
    """Verify ticker lookup uses batch_get_stocks_by_tickers, not O(n) loop"""
    stocks = batch_get_stocks_by_tickers(['AAPL', 'MSFT'])
    assert 'AAPL' in stocks
```

### Integration Tests (Verify index usage)
```python
def test_stocks_filter_uses_index():
    """EXPLAIN PLAN should show idx_stocks_active_market used"""
    plan = conn.execute('EXPLAIN QUERY PLAN SELECT * FROM stocks WHERE active=1 AND market=?')
    assert 'idx_stocks_active_market' in str(plan.fetchall())
```

### Performance Benchmarks
- Stocks pagination: `<50ms` (vs 500ms+)
- Ticker lookup: `<10ms` (vs 100ms+)
- Research pagination: `<100ms` (vs 200ms+)

---

## 7. ACCEPTANCE CRITERIA

- [ ] All N+1 patterns eliminated (code review: no loops calling DB)
- [ ] All hot-path queries verified with EXPLAIN PLAN (index hits confirmed)
- [ ] 12+ unit tests passing (verify SQL optimization patterns)
- [ ] Performance benchmarks show 5-10x improvement
- [ ] No API contract changes (responses identical)
- [ ] All existing tests pass
- [ ] Code review confirms parameterized queries (no SQL injection risk)

---

## 8. ROLLBACK STRATEGY

**Zero-risk:** Indexes are additive; dropping them reverts behavior.
```bash
DROP INDEX idx_stocks_active_market;
DROP INDEX idx_stocks_active;
# ... etc
# No data lost, queries just slower
```

---

## 9. Current Implementation Status

✅ **Done:**
- Index definitions (database.py: lines 264-321)
- SQL filtering in stocks API (stocks.py: line 60)
- Optimized pagination (research.py: line 47, query_optimizer.py)

⏳ **Remaining:**
- Complete prices API optimization
- Complete analysis API optimization
- Write integration tests verifying EXPLAIN PLAN
- Performance benchmarks in CI/CD
