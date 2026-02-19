# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## User Story

---

## User Story: Remove Root-Level Duplicate Module Files

**Story ID:** VO-011-cleanup (prerequisite hygiene task)

---

### User Story

> As a **backend developer**, I want the root-level `ai_analytics.py` and `ai_providers.py` deleted and all imports redirected to `backend/core/`, so that there is a single source of truth for AI analytics logic and I never accidentally run the degraded, misconfigured version.

---

### Acceptance Criteria

- [ ] `/ai_analytics.py` (493 lines, root) is deleted from the repository
- [ ] `/ai_providers.py` (302 lines, root) is deleted from the repository
- [ ] `dashboard.py` imports updated: all `from ai_analytics import ...` and `from ai_providers import ...` become `from backend.core.ai_analytics import ...` and `from backend.core.ai_providers import ...`
- [ ] `backend/core/ai_analytics.py` internal import (`from ai_providers import AIProviderFactory`) updated to `from backend.core.ai_providers import AIProviderFactory`
- [ ] The app starts without `ImportError` after deletion
- [ ] `test_import_refactor.py` passes — root-level imports no longer resolve

---

### Priority Reasoning

**High.** The root `ai_analytics.py` uses a hardcoded `DB_PATH = 'stock_news.db'` instead of `Config.DB_PATH`, and is missing 71 lines of fallback/error-handling logic present in the canonical version. Any code path hitting the root module silently degrades. This is an active maintenance hazard — two files diverging over time with no clear ownership — and it blocks confident refactoring of the analytics layer.

---

### Complexity

**2 / 5** — Pure deletion + import path updates. No logic changes. Risk is low because `test_import_refactor.py` already asserts the correct end state. Verify app boot and run existing tests to confirm.
