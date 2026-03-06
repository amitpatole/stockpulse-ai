# Technical Design: Missing Scheduler Jobs (11+ Implementation)

## Overview
TickerPulse currently has 7/18+ scheduler jobs implemented. This spec outlines implementation of 11 missing jobs focused on indicator updates, price alerts, portfolio analysis, and sentiment aggregation with built-in retry logic.

---

## Approach

**Strategy**: Use existing APScheduler infrastructure (`backend/scheduler.py`) + job helper functions (`backend/jobs/_helpers.py`) to implement missing jobs following the established pattern.

**Retry Logic**: Leverage APScheduler's `coalesce=True`, `max_instances=1`, `misfire_grace_time=300` defaults. For agent failures, implement exponential backoff via `job_timer` context manager error handling + manual retry scheduling.

**Database**: Reuse existing tables (`ai_ratings`, `alerts`, `stocks`, `agent_runs`, `job_history`, `cost_tracking`). Add minimal schema changes.

---

## Files to Modify/Create

### Modify
1. **`backend/jobs/__init__.py`** - Register 11 new jobs in `register_all_jobs()`
2. **`backend/database.py`** - Add 2 new tables for indicator cache & rebalance history

### Create (11 new job modules)
3. **`backend/jobs/daily_indicator_update.py`** - Cache technical indicators (SMA, EMA, RSI, MACD, BB) for all stocks
4. **`backend/jobs/price_alert_check.py`** - Scan `stocks` for price breaches vs. user-configured thresholds
5. **`backend/jobs/portfolio_rebalancing.py`** - Calculate rebalance targets, generate trades (write to `job_history`)
6. **`backend/jobs/sentiment_aggregation.py`** - Aggregate `news` sentiment → ticker summary in `ai_ratings`
7. **`backend/jobs/intraday_volume_spike.py`** - Detect abnormal volume during market hours
8. **`backend/jobs/correlation_monitor.py`** - Track stock correlations for sector rotation signals
9. **`backend/jobs/earnings_calendar_check.py`** - Scan upcoming earnings, flag in `alerts`
10. **`backend/jobs/volatility_regime_update.py`** - Calculate VIX-like score → market regime
11. **`backend/jobs/ai_rating_refresh.py`** - Refresh stale `ai_ratings` by running Analyst agent
12. **`backend/jobs/cost_ledger_summary.py`** - Daily/weekly cost aggregation for billing
13. **`backend/jobs/watchlist_health_check.py`** - Validate watchlist staleness, flag delisted tickers

---

## Data Model Changes

### New Tables

**`indicator_cache`** (lines 200-220 in database.py)
```sql
CREATE TABLE indicator_cache (
    id              INTEGER PRIMARY KEY,
    ticker          TEXT NOT NULL UNIQUE,
    sma_20          REAL,
    sma_50          REAL,
    ema_12          REAL,
    ema_26          REAL,
    rsi_14          REAL,
    macd_line       REAL,
    macd_signal     REAL,
    bb_upper        REAL,
    bb_lower        REAL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**`rebalance_history`** (lines 220-235)
```sql
CREATE TABLE rebalance_history (
    id              INTEGER PRIMARY KEY,
    portfolio_date  TEXT NOT NULL,
    ticker          TEXT NOT NULL,
    current_weight  REAL,
    target_weight   REAL,
    action          TEXT,  -- BUY|SELL|HOLD
    shares          REAL,
    executed        INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Modified Tables
- `ai_ratings`: Add `sentiment_score_agg`, `correlation_score`, `earnings_date` (nullable)
- `alerts`: No changes (reuse existing schema)

---

## Job Schedules

| Job | Trigger | Frequency | Description |
|-----|---------|-----------|-------------|
| daily_indicator_update | cron | 8:00 AM ET | Refresh technical indicators for all stocks |
| price_alert_check | interval | Every 30 min (market hours) | Check price breaches |
| portfolio_rebalancing | cron | Weekly (Sunday 10 AM) | Calculate rebalance targets |
| sentiment_aggregation | interval | Every 2 hours | Aggregate news sentiment |
| intraday_volume_spike | interval | Every 5 min (market hours) | Detect volume anomalies |
| correlation_monitor | cron | Daily (9:00 AM ET) | Update stock correlations |
| earnings_calendar_check | cron | Daily (8:30 AM ET) | Flag upcoming earnings |
| volatility_regime_update | interval | Every 1 hour | Calculate market volatility |
| ai_rating_refresh | cron | Every 4 hours | Refresh stale ratings |
| cost_ledger_summary | cron | 11:00 PM ET daily | Aggregate costs |
| watchlist_health_check | cron | Daily (9:15 AM ET) | Validate watchlist health |

---

## Testing Strategy

**Unit Tests** (`backend/tests/test_scheduler_jobs_new.py`)
- Mock agent responses, price feeds
- Test indicator calculation accuracy
- Test alert generation logic
- Test portfolio math (weights, rebalance targets)
- Test retry behavior on agent failure

**E2E Tests** (`e2e/scheduler.spec.ts`)
- Trigger each job manually via API `/api/scheduler/jobs/{id}/trigger`
- Verify job_history records created
- Verify database state changes (indicator_cache, rebalance_history)
- Verify SSE events broadcast

**Integration Tests**
- Run all jobs in sequence, verify no race conditions
- Test database lock handling under concurrent execution
- Test recovery from partial failures

---

## API Endpoints (Reuse Existing)

All jobs exposed via existing scheduler routes:
- `GET /api/scheduler/jobs` - List all jobs with status
- `POST /api/scheduler/jobs/{id}/trigger` - Manual execution
- `GET /api/scheduler/jobs/{id}/history` - Job history

No new endpoints required.
