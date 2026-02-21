# VO-336: Timezone Display Bug in Data Provider Fallback Chain for Non-US Locales

**Type:** Bug
**Area:** Data Provider Fallback Chain
**Reported by:** QA (code review / testing)
**Date:** 2026-02-21

---

## User Story

As a **trader or analyst using Virtual Office from a non-US locale** (e.g., India, EU, Japan, Australia),
I want **all market data timestamps to be correctly normalized to UTC before being served**,
so that **I can trust the timestamps shown for quotes, historical prices, and agent events — and convert them accurately to my local time without off-by-hours errors**.

---

## Background

The data provider fallback chain (Polygon → Finnhub → Alpha Vantage → Yahoo Finance) converts Unix timestamps to Python `datetime` objects in multiple places. None of these calls specify `tz=timezone.utc`, so the conversion uses the server's local timezone instead of UTC. Combined with widespread use of the deprecated `datetime.utcnow()` — which returns a naive (timezone-unaware) datetime — timestamps are silently wrong or ambiguous for any non-UTC user. The problem compounds when the fallback chain activates, since each provider independently performs the same broken conversion.

**Key affected locations:**
- `backend/data_providers/yfinance_provider.py:194` — `datetime.fromtimestamp(ts)` (no tz)
- `backend/data_providers/polygon_provider.py:155,178,198` — `datetime.fromtimestamp(...)` (no tz)
- `backend/data_providers/finnhub_provider.py:135` — `datetime.fromtimestamp(ts)` (no tz)
- `backend/api/analysis.py:164` — deprecated `datetime.utcfromtimestamp()`
- `backend/agents/base.py:100`, `backend/agents/crewai_engine.py:201` — `datetime.utcnow().isoformat()` (naive, no `Z` suffix)
- ~20+ additional `datetime.utcnow()` usages across API routes and agent files

---

## Acceptance Criteria

- [ ] All `datetime.fromtimestamp(ts)` calls in every data provider are updated to `datetime.fromtimestamp(ts, tz=timezone.utc)`
- [ ] All `datetime.utcnow()` calls are replaced with `datetime.now(timezone.utc)` across the entire backend
- [ ] All `datetime.utcfromtimestamp()` calls are replaced with `datetime.fromtimestamp(..., tz=timezone.utc)`
- [ ] All datetime values serialized to JSON include an explicit UTC offset (ISO8601 format with `+00:00` or `Z`), never a naive string
- [ ] Converting the same Unix timestamp through any provider in the fallback chain yields the identical UTC datetime value
- [ ] Existing tests in `backend/tests/test_data_provider_fallback.py` continue to pass
- [ ] New tests assert that datetime objects returned by each provider are timezone-aware (`tzinfo is not None`)
- [ ] QA confirms correct timestamp display in at least two non-US locales (e.g., IST +05:30, CET +01:00)

---

## Priority Reasoning

**High.** This is a data correctness bug in a trading application. An off-by-hours timestamp on a quote or a news event can directly affect a trading decision. The bug silently affects every non-US user and gets worse during provider fallback (each provider independently introduces the same error, potentially with different offsets depending on server config). The fix is well-bounded and carries low regression risk — no schema changes, no API contract changes.

---

## Estimated Complexity: 2 / 5

The fix is mechanical: a targeted find-and-replace of deprecated/naive datetime calls across the backend. No architectural changes are needed. A grep pass before and after is sufficient to verify completeness. Writing timezone-aware assertions for existing tests adds minimal effort.

**Effort breakdown:**
- Fix all `fromtimestamp` / `utcnow` / `utcfromtimestamp` calls across providers and agents: ~2–3 hrs
- Add timezone-aware assertions to existing provider tests: ~1 hr
- QA validation across two non-US locales: ~1 hr
