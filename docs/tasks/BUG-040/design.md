# BUG-040: Memory Leak in Export Feature After Prolonged Usage

## Technical Design

**Author:** Diana Torres, Architect
**Story ID:** BUG-040
**Complexity:** 2 / 5

---

### Root Cause

Two confirmed leak sources:

1. **Unmanaged `requests.Session` objects in data providers.** Six providers (`alpha_vantage_provider.py`, `yfinance_provider.py`, `polygon_provider.py`, `finnhub_provider.py`, `ai_analytics.py`, `stock_monitor.py`) instantiate `self.session = requests.Session()` in `__init__` and never call `.close()`. The `reddit_scanner.py` tool creates a local `session` inside `_scan()` without a finally-close. Each un-closed session leaks a connection pool and associated socket descriptors for the lifetime of the object (or forever in the scanner's case).

2. **CrewAI `Crew` objects accumulate memory across repeated export cycles.** In `crewai_engine.py:run_crew()` (lines 224–231), a `Crew` is created with `memory=True` on each agent. After `kickoff()` the `crew` variable goes out of scope but CPython's reference counting is not guaranteed to collect it promptly, and CrewAI's internal vector store (used by `memory=True`) may hold references that prevent GC entirely.

---

### Approach

Fix is mechanical and localised — no architectural changes.

1. **Data providers:** Add `close()` and `__del__` methods to each provider class; implement `__enter__`/`__exit__` so callers can use them as context managers where appropriate. No callers need to change unless they already new-up providers inside a loop.

2. **Reddit scanner:** Wrap the local session in a `try/finally` to guarantee `.close()` on both the happy path and exception path.

3. **CrewAI engine:** After `crew.kickoff()`, explicitly `del crew` and call `gc.collect()`. Also disable per-agent `memory=True` — this feature is not exercised by current export flows and is the primary source of vector-store accumulation.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/data_providers/alpha_vantage_provider.py` | Add `close()`, `__del__`, `__enter__`, `__exit__` to `AlphaVantageProvider` |
| `backend/data_providers/yfinance_provider.py` | Same pattern for `YFinanceProvider` |
| `backend/data_providers/polygon_provider.py` | Same pattern for `PolygonProvider` |
| `backend/data_providers/finnhub_provider.py` | Same pattern for `FinnhubProvider` |
| `backend/core/ai_analytics.py` | Add `close()` + `__del__` to `AIAnalytics` |
| `backend/core/stock_monitor.py` | Add `close()` + `__del__` to `StockMonitor` |
| `backend/agents/tools/reddit_scanner.py` | Wrap local `session` in `try/finally: session.close()` inside `_scan()` |
| `backend/agents/crewai_engine.py` | Set `memory=False` on `CrewAgent` construction; add `del crew; gc.collect()` after `kickoff()` |

No new files needed.

---

### Data Model Changes

None.

---

### API Changes

None.

---

### Frontend Changes

None.

---

### Testing Strategy

| Scenario | How |
|---|---|
| Session closed on happy path | Unit: mock `requests.Session`; call provider `_get()`; assert `session.close()` called on the mock |
| Session closed on exception | Unit: make `session.get()` raise; assert `session.close()` still called |
| Reddit scanner closes session | Unit: mock `Session` in `reddit_scanner._scan()`; force exception mid-scan; assert `.close()` called |
| CrewAI memory does not grow across cycles | Integration: run `run_crew()` 50× in a loop; snapshot RSS before and after via `resource.getrusage()`; assert growth < 50 MB |
| No open sockets after export cycle | Integration: run full export job; assert `psutil.Process().connections()` count returns to baseline |
| Context manager protocol on providers | Unit: `with AlphaVantageProvider(...) as p: pass`; assert `p.session` is closed |
| QA regression — 50 consecutive export cycles | Manual / CI load script: run download tracker job 50× via `POST /api/jobs/download-tracker/trigger`; observe RSS with `ps` between cycles |
