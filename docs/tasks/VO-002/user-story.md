# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## User Story

---

## User Story: Remove Root-Level Duplicate AI Modules

**As a** backend developer maintaining the Virtual Office codebase,
**I want** the root-level `ai_analytics.py` and `ai_providers.py` deleted and all imports updated to `backend.core.*`,
**so that** there is a single canonical source of truth for AI logic, eliminating the risk of diverged behavior, silent bugs, and wasted maintenance effort.

---

### Acceptance Criteria

- [ ] `/ai_analytics.py` (493 lines) is deleted from the project root
- [ ] `/ai_providers.py` (302 lines) is deleted from the project root
- [ ] `dashboard.py` imports updated:
  - `from ai_analytics import StockAnalytics` → `from backend.core.ai_analytics import StockAnalytics` (3 occurrences)
  - `from ai_providers import test_provider_connection` → `from backend.core.ai_providers import test_provider_connection`
  - `from ai_providers import AIProviderFactory` → `from backend.core.ai_providers import AIProviderFactory`
- [ ] No remaining `import ai_analytics` or `import ai_providers` references exist anywhere in the codebase
- [ ] `dashboard.py` still runs without import errors after the change
- [ ] No other functionality is altered — this is purely a structural cleanup

---

### Priority Reasoning

**High.** The root `ai_analytics.py` is 71 lines behind `backend/core/` — it's missing the two-tier Yahoo Finance fallback, sentiment error handling, price change metrics, DB result caching, and frontend-normalized score scaling. Any code path routed through `dashboard.py` silently gets degraded, inconsistent behavior. `ai_providers.py` is identical today but will diverge the moment someone edits only one copy. This is a maintenance hazard with a cheap fix.

---

### Complexity: 2 / 5

Low risk. One file (`dashboard.py`) needs import updates — all backend code already uses the correct paths. No logic changes, no new tests needed. Verify `dashboard.py` imports resolve and the app starts cleanly.
