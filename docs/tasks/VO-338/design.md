# VO-338: Timezone display bug in data provider fallback chain for non-US locales

## Technical Design

A comprehensive design spec already exists at `docs/tasks/VO-336/design.md`. Here is my architecture review based on direct codebase analysis:

---

## VO-336 Technical Design Spec — Timezone Display Bug

### 1. Approach

Mechanical, three-rule sweep across the backend. No schema changes, no API contract breaks, no new dependencies — `timezone.utc` from the standard library is already available everywhere.

**Three substitution rules:**
- `datetime.fromtimestamp(ts)` → `datetime.fromtimestamp(ts, tz=timezone.utc)`
- `datetime.utcnow()` → `datetime.now(timezone.utc)`
- `datetime.utcfromtimestamp(ts)` → `datetime.fromtimestamp(ts, tz=timezone.utc)`

As a bonus, all `+ 'Z'` string appends (e.g. `app.py:150`) can be dropped — `.isoformat()` on a UTC-aware datetime already emits `+00:00`.

---

### 2. Files to Modify

**Data providers (root of the bug) — ~15 call sites:**
- `backend/data_providers/finnhub_provider.py` — line 135 (`fromtimestamp`)
- `backend/data_providers/polygon_provider.py` — lines 155, 178, 198 (`fromtimestamp` ×3, plus `datetime.now()` date-range calls)
- `backend/data_providers/yfinance_provider.py` — line 194 (`fromtimestamp` + `datetime.now()` fallback)
- `backend/data_providers/alpha_vantage_provider.py` — `datetime.strptime(...)` bar/quote calls → add `.replace(tzinfo=timezone.utc)`
- `backend/data_providers/custom_provider.py` — fix the template comment so new providers don't copy the bug

**Agent event timestamps (~14 call sites):**
- `backend/agents/base.py` — lines 100, 105, 120
- `backend/agents/crewai_engine.py` — lines 201, 212, 227, 239, 294, 312
- `backend/agents/openclaw_engine.py` — lines 166, 178, 202, 213, 250, 268, 288, 301

**API routes & jobs (~10 call sites):**
- `backend/api/analysis.py:164` — `utcfromtimestamp`
- `backend/app.py:150`, `backend/api/agents.py:524`, `backend/api/downloads.py:97,192`
- `backend/scheduler.py:215`
- `backend/jobs/_helpers.py`, `daily_summary.py`, `morning_briefing.py`, `regime_check.py`, `technical_monitor.py`, `weekly_review.py`, `download_tracker.py`, `reddit_scanner.py`

**Core / tools:**
- `backend/core/stock_monitor.py:358`, `backend/agents/tools/reddit_scanner.py`, `backend/agents/tools/news_fetcher.py`
- `backend/agents/{researcher,investigator,download_tracker}_agent.py`

**Tests:**
- `backend/tests/test_data_provider_fallback.py` — update `sample_quote()` line 41 to `datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)`
- **New:** `backend/tests/test_datetime_utc.py`

---

### 3. Data Model Changes

None. `Quote.timestamp` is typed `datetime` and already accepts tz-aware values. `PriceBar.timestamp` is a raw `int` Unix epoch — untouched.

---

### 4. API Changes

No new or removed endpoints. JSON responses where `.isoformat()` is called will emit `2024-01-15T10:00:00+00:00` instead of the bare `2024-01-15T10:00:00`. Non-breaking — strictly more correct ISO8601.

---

### 5. Frontend Changes

None. JavaScript `new Date("2024-01-15T10:00:00+00:00")` already parses ISO8601 with offset correctly. The previous naive string was silently interpreted as local time — the actual bug for non-US users. The fix is transparent to all frontend components.

---

### 6. Testing Strategy

**Existing regression:** `pytest backend/tests/test_data_provider_fallback.py -v` must pass after updating `sample_quote()`. No test logic changes, just the fixture timestamp.

**New `test_datetime_utc.py`:**
1. `test_quote_timestamp_is_utc_aware` — for each mock provider stub, assert `result.timestamp.tzinfo is not None` and `result.timestamp.tzinfo == timezone.utc`
2. `test_same_unix_ts_all_providers_identical` — same Unix epoch through all four provider stubs must yield the same `datetime`
3. `test_isoformat_has_utc_offset` — assert `quote.timestamp.isoformat()` matches `+00:00$`

**CI verification gate:**
```bash
# Must return zero results after the fix
grep -rn "datetime\.utcnow\(\)\|utcfromtimestamp\|fromtimestamp([^,)]*)" \
  backend/ --include="*.py"
```

---

The fix is scoped to ~35 call sites across ~20 files. All changes are mechanical and grep-verifiable — zero risk of partial fixes slipping through with the CI gate in place.
