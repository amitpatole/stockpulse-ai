# Technical Specification: Database Query Optimization

**Status**: In Progress
**Target Completion**: Sprint 4
**Priority**: High (Critical Path)

---

## 1. APPROACH

### High-Level Strategy
Optimize database queries by eliminating N+1 patterns, adding strategic indexes, and ensuring SQL-side filtering. Current codebase has good index infrastructure in `database.py` but APIs are still filtering/searching in Python.

**Three-Phase Approach:**
1. **Phase 1 - N+1 Elimination**: Fix API endpoints that load all records then filter in Python
2. **Phase 2 - Index Verification**: Confirm all hot-path queries use indexes; add missing composite indexes
3. **Phase 3 - Query Profiling**: Add EXPLAIN PLAN logging to identify remaining bottlenecks

### Key Principles
- **SQL-Side Filtering**: WHERE clauses in queries, not Python loops
- **Batch Queries**: Use IN clauses for multiple lookups, not loop + individual queries
- **Column Selection**: SELECT only needed columns, avoid SELECT *
- **Composite Indexes**: For WHERE + ORDER BY + LIMIT patterns
- **Connection Pooling**: Reuse db_session() context manager, avoid duplicating connections

---

## 2. FILES TO MODIFY/CREATE

### Modify (4 files)
| File | Changes | Reason |
|------|---------|--------|
| `backend/api/stocks.py` | Replace `get_all_stocks()` filtering with SQL-side `get_stocks_with_filter()` | Fix N+1 on market filter |
| `backend/api/prices.py` | Replace `get_all_stocks()` + linear search with `batch_get_stocks_by_tickers()` | Eliminate full scan for single ticker |
| `backend/api/analysis.py` | Use `get_cached_ratings_optimized()` instead of raw SQL; add EXPLAIN logging | Ensure index usage on ai_ratings |
| `backend/api/research.py` | Use `get_research_briefs_by_ticker()` pagination; verify composite index hit | Confirm ticker+created_at index usage |

### Create (2 files)
| File | Purpose |
|------|---------|
| `backend/core/query_profiler.py` | EXPLAIN PLAN logging middleware to identify slow queries |
| `backend/tests/test_query_optimization_integration.py` | E2E tests verifying SQL plans use indexes (not full table scans) |

### Enhance (1 file)
| File | Addition |
|------|----------|
| `backend/database.py` | Add missing composite indexes for alerts, news secondary paths |

---

## 3. DATA MODEL CHANGES

### New/Modified Indexes
```sql
-- NEW: Missing composite indexes for hot paths

-- news table: ticker + created_at + sentiment for filtering/sorting
CREATE INDEX IF NOT EXISTS idx_news_ticker_sentiment_date
ON news (ticker, sentiment_label, created_at DESC);

-- alerts table: ticker + created_at for alert history queries
CREATE INDEX IF NOT EXISTS idx_alerts_ticker_created
ON alerts (ticker, created_at DESC);

-- alerts table: news_id lookup with status
CREATE INDEX IF NOT EXISTS idx_alerts_news_status
ON alerts (news_id, alert_type);

-- ai_ratings: ticker + updated_at for cache staleness checks
CREATE INDEX IF NOT EXISTS idx_ai_ratings_ticker_updated
ON ai_ratings (ticker, updated_at DESC);

-- research_briefs: ticker + agent_name for filtering by generation source
CREATE INDEX IF NOT EXISTS idx_research_briefs_ticker_agent
ON research_briefs (ticker, agent_name, created_at DESC);

-- cost_tracking: date + agent for dashboard aggregations
CREATE INDEX IF NOT EXISTS idx_cost_tracking_date_agent_cost
ON cost_tracking (date, agent_name, estimated_cost);

-- job_history: efficient status filtering by date range
CREATE INDEX IF NOT EXISTS idx_job_history_status_executed
ON job_history (status, executed_at DESC);
```

### No Schema Changes Required
- All tables already have proper foreign keys
- No new columns needed
- Soft-delete via `active` flag is already indexed

---

## 4. API CHANGES

### Modified Endpoints (No Breaking Changes)

**GET /api/stocks** - Response format unchanged, query path optimized
```javascript
// BEFORE: O(n) - loads ALL stocks, filters in Python
stocks = get_all_stocks()  // 1000+ records
stocks = [s for s in stocks if s.get('market') == market]  // Python filter

// AFTER: O(log n) - SQL WHERE clause + index
stocks, total = get_stocks_with_filter(market, limit, offset)  // Uses idx_stocks_active_market
```

**GET /api/prices/<ticker>** - Same response, single-ticker lookup optimized
```javascript
// BEFORE: O(n) scan
all_stocks = get_all_stocks()  // 1000+ records
stock = next((s for s in all_stocks if s['ticker'] == ticker))  // Linear search

// AFTER: O(log n) batch lookup
stocks = batch_get_stocks_by_tickers([ticker])  // Uses idx_stocks_active
stock = stocks.get(ticker)
```

**GET /api/analysis/ratings** - Uses existing index strategy
```javascript
// USES: idx_ai_ratings_ticker (already defined)
// ENHANCED: Add EXPLAIN logging to verify index hit
```

**GET /api/research/briefs** - Pagination with composite index
```javascript
// USES: idx_research_briefs_ticker_created (already defined)
// ADDS: idx_research_briefs_ticker_agent for agent filtering
```

---

## 5. FRONTEND CHANGES

**No changes required.**

- Frontend already uses pagination parameters
- Query optimization is backend-only
- Response format stays identical

---

## 6. TESTING STRATEGY

### Unit Tests (backend/tests/test_query_optimization_integration.py)
**12+ tests verifying:**
- ✅ Stocks pagination with market filter uses SQL WHERE (not Python)
- ✅ Single ticker lookup uses batch query (not full scan)
- ✅ Ratings endpoint only selects needed columns
- ✅ Research briefs use composite (ticker, created_at) index
- ✅ No N+1 patterns when fetching related data

### Integration Tests (test_database_optimization.py - Enhanced)
**8+ tests verifying index effectiveness:**
- ✅ EXPLAIN PLAN shows index usage (not full table scan)
- ✅ Composite index is used for (WHERE ticker AND ORDER BY created_at)
- ✅ Foreign key lookups use index on PK
- ✅ Pagination queries return correct has_next/has_previous

### Performance Benchmarks (New)
**Measure latency before/after:**
```python
# Benchmark: get_stocks with market filter
# BEFORE: 50ms (1000 stock records)
# AFTER: 5ms (index seek)
# TARGET: < 10ms on 10k+ records

# Benchmark: get_price (single ticker)
# BEFORE: 40ms (full scan)
# AFTER: 2ms (batch lookup)
# TARGET: < 5ms
```

### E2E Tests (Playwright)
**Verify UI latency improvement:**
- ✅ /stocks page loads in < 1 second (with 100 records)
- ✅ Stock filter by market responds in < 300ms
- ✅ Price widget updates in < 100ms

---

## 7. ACCEPTANCE CRITERIA

- [ ] All N+1 patterns eliminated (no loops calling DB query)
- [ ] All hot-path queries verified with EXPLAIN PLAN using indexes
- [ ] New composite indexes added to database.py
- [ ] 12+ optimization tests all passing
- [ ] Performance benchmarks show 5-10x latency improvement
- [ ] No API contract changes (responses identical)
- [ ] All existing tests still pass
- [ ] Code review confirms proper parameterized queries (no SQL injection risk)

---

## 8. ROLLBACK STRATEGY

**Zero-risk rollback:**
1. Drop new indexes (don't drop data)
2. Revert API code changes
3. Restart Flask server
4. No data migration needed

New indexes are additive; dropping them doesn't affect functionality.

---

## 9. MONITORING & ALERTING

Post-deployment, monitor:
```python
# Query latency percentiles (p50/p95/p99)
# - GET /api/stocks: target p99 < 50ms
# - GET /api/prices/<ticker>: target p99 < 20ms
# - GET /api/analysis/ratings: target p99 < 100ms

# Index usage rate
# - Verify idx_stocks_active_market is hit on /stocks
# - Verify idx_ai_ratings_ticker is hit on /analysis/ratings

# Database size monitoring
# - Indexes will add ~50-100MB storage (negligible)
# - Monitor WAL file growth (WAL should auto-checkpoint)
```

---

## 10. DEPENDENCIES & BLOCKERS

**None.** All utilities already exist:
- ✅ `query_optimizer.py` - Helper functions written
- ✅ `database.py` - Index infrastructure ready
- ✅ `db_session()` - Connection pooling available

---

## Summary

**Before**: APIs fetch all data, filter in Python → O(n) slow
**After**: Optimized SQL with indexes → O(log n) fast
**Impact**: 5-10x latency improvement, zero breaking changes
