# VO-336 Design Spec — Timezone Display Bug (Data Provider Fallback Chain)

## 1. Approach

Mechanical find-and-replace of all naive datetime construction across the backend, enforcing a single invariant: **every `datetime` object produced internally is UTC-aware**. No schema changes, no API contract changes — only the representation of timestamps changes (from naive to `+00:00` ISO8601). The fix is applied in three passes:

1. **Data providers** — the root of the bug. Fix timestamp construction in all four provider implementations so `Quote.timestamp` is always `timezone.utc`-aware.
2. **Agent event timestamps** — `started_at` / `completed_at` fields serialized to JSON; replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
3. **Remaining backend callsites** — jobs, API routes, core utilities that emit naive datetimes or use the deprecated `utcnow()` / `utcfromtimestamp()` APIs.

All replacements follow three mechanical rules:
- `datetime.fromtimestamp(ts)` → `datetime.fromtimestamp(ts, tz=timezone.utc)`
- `datetime.utcnow()` / `datetime.now()` → `datetime.now(timezone.utc)`
- `datetime.utcfromtimestamp(ts)` → `datetime.fromtimestamp(ts, tz=timezone.utc)`

`.isoformat()` on a `timezone.utc`-aware datetime already produces `+00:00`; drop all manual `+ 'Z'` string appends.

---

## 2. Files to Modify

**Data provider layer (primary fix):**
- `backend/data_providers/finnhub_provider.py` — line 97 (`datetime.now()`), line 135 (`datetime.fromtimestamp(ts)`)
- `backend/data_providers/polygon_provider.py` — lines 114, 139–140, 155, 178–179, 185–186, 198, 209–210
- `backend/data_providers/yfinance_provider.py` — lines 106, 194, 237
- `backend/data_providers/alpha_vantage_provider.py` — lines 109, 157, 218
- `backend/data_providers/custom_provider.py` — update the `datetime.fromtimestamp` example comment (line 108)

**Agent event timestamps:**
- `backend/agents/base.py` — lines 100, 105, 120
- `backend/agents/crewai_engine.py` — lines 201, 212, 227, 239, 294, 312
- `backend/agents/openclaw_engine.py` — lines 166, 178, 202, 213, 250, 268, 288, 301

**API routes:**
- `backend/api/analysis.py` — line 164 (`datetime.utcfromtimestamp`)
- `backend/app.py` — line 150
- `backend/api/agents.py` — line 524
- `backend/api/downloads.py` — lines 97, 192

**Jobs:**
- `backend/jobs/_helpers.py`, `daily_summary.py`, `technical_monitor.py`, `weekly_review.py`, `morning_briefing.py`, `regime_check.py`, `download_tracker.py`, `reddit_scanner.py`

**Core / agent tools:**
- `backend/core/ai_analytics.py`, `backend/core/stock_monitor.py`
- `backend/agents/researcher_agent.py`, `backend/agents/investigator_agent.py`, `backend/agents/download_tracker_agent.py`
- `backend/agents/tools/reddit_scanner.py`, `backend/agents/tools/news_fetcher.py`

**Tests:**
- `backend/tests/test_data_provider_fallback.py` — update `sample_quote` fixture to use `datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)`

**New test file:**
- `backend/tests/test_datetime_utc.py`

---

## 3. Data Model Changes

None. `Quote.timestamp` is already typed as `datetime`; making it consistently UTC-aware is a runtime correctness fix, not a schema change. `PriceBar.timestamp` is a raw Unix `int` — no change needed.

---

## 4. API Changes

No new or removed endpoints. JSON responses that serialize `datetime.isoformat()` will now emit `2024-01-15T10:00:00+00:00` instead of `2024-01-15T10:00:00`. This is a **non-breaking improvement** — ISO8601 with explicit offset is strictly more correct and parseable by all clients.

---

## 5. Frontend Changes

None. The frontend already receives ISO8601 strings; explicit `+00:00` is valid ISO8601 and handled identically by JavaScript `new Date(str)`.

---

## 6. Testing Strategy

**Existing tests:** `test_data_provider_fallback.py` must continue to pass. The `sample_quote` fixture is updated to use a UTC-aware `datetime`; no test logic changes otherwise.

**New tests in `test_datetime_utc.py`:**
- For each mock provider (`finnhub`, `polygon`, `yfinance`, `alpha_vantage`): assert `quote.timestamp.tzinfo is not None` and `quote.timestamp.tzinfo == timezone.utc`
- Assert that the same Unix timestamp through any provider yields an identical `datetime` object
- Assert `datetime.isoformat()` output contains `+00:00`

**Verification grep:** After the fix, `git grep -n "fromtimestamp\|utcnow\|utcfromtimestamp\|datetime\.now()" -- backend/` must return zero matches (except `datetime.now(timezone.utc)` and `datetime.fromtimestamp(ts, tz=timezone.utc)` forms).
