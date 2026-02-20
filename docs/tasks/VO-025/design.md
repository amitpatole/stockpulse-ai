# VO-025: Memory leak in export feature after prolonged usage

## Technical Design

Here is the design spec I've written to `docs/tasks/BUG-040/design.md`:

---

## Technical Design: BUG-040 — Memory Leak in Export Feature

### Root Cause

Two confirmed leak sources in the codebase:

**1. Unmanaged `requests.Session` objects.** Six providers create `self.session = requests.Session()` in `__init__` and never call `.close()`:
- `backend/data_providers/{alpha_vantage,yfinance,polygon,finnhub}_provider.py`
- `backend/core/{ai_analytics,stock_monitor}.py`

`reddit_scanner.py:_scan()` also instantiates a local `session` without a `finally` close — leaks on every exception path.

**2. CrewAI `Crew` object accumulation.** `crewai_engine.py` (lines 224–231) constructs a `Crew` with `memory=True` per agent on every `run_crew()` call. CrewAI's internal vector store holds back-references that block GC, compounding across repeated export cycles.

---

### Approach

Entirely mechanical — no architectural changes.

1. **Providers:** Add `close()`, `__del__`, and `__enter__`/`__exit__` to all six provider classes. This is the same pattern already used by `openclaw_engine.py`.
2. **Reddit scanner:** Wrap the local `session` in `try/finally: session.close()` inside `_scan()`.
3. **CrewAI engine:** Set `memory=False` on `CrewAgent` construction (not used by export flows). Add `del crew; gc.collect()` immediately after `kickoff()`.

### Files to Modify

| File | Change |
|---|---|
| `backend/data_providers/alpha_vantage_provider.py` | Add `close()`, `__del__`, `__enter__`/`__exit__` |
| `backend/data_providers/yfinance_provider.py` | Same |
| `backend/data_providers/polygon_provider.py` | Same |
| `backend/data_providers/finnhub_provider.py` | Same |
| `backend/core/ai_analytics.py` | Add `close()` + `__del__` |
| `backend/core/stock_monitor.py` | Add `close()` + `__del__` |
| `backend/agents/tools/reddit_scanner.py` | `try/finally: session.close()` in `_scan()` |
| `backend/agents/crewai_engine.py` | `memory=False` on agents; `del crew; gc.collect()` post-kickoff |

### Data Model / API / Frontend Changes

None — purely backend resource management.

### Testing Strategy

- **Unit:** Mock `requests.Session`; assert `.close()` is called on both happy and exception paths for each provider and the scanner.
- **Unit:** Context manager protocol — `with AlphaVantageProvider(...) as p: pass` → assert session is closed.
- **Integration (memory):** Run `run_crew()` 50× in a loop; snapshot RSS via `resource.getrusage()` before/after; assert growth < 50 MB.
- **Integration (sockets):** Run a full download tracker job; assert `psutil.Process().connections()` count returns to baseline.
- **QA manual:** 50 consecutive export cycles via `POST /api/jobs/download-tracker/trigger`; observe RSS with `ps` between cycles.
