# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## User Story

**User Story: Remove Root-Level AI Module Duplicates**

---

**As a** backend developer maintaining the Virtual Office codebase,
**I want** the root-level `ai_analytics.py` and `ai_providers.py` deleted and all imports redirected to `backend/core/`,
**so that** there is a single source of truth for AI analytics logic, eliminating the risk of silent divergence, inconsistent output formats, and missed bug fixes propagating to only half the system.

---

## Acceptance Criteria

- [ ] `/ai_analytics.py` (493 lines) is deleted from the project root
- [ ] `/ai_providers.py` (302 lines) is deleted from the project root
- [ ] `dashboard.py` imports updated: all `from ai_analytics import ...` → `from backend.core.ai_analytics import ...`
- [ ] `dashboard.py` imports updated: all `from ai_providers import ...` → `from backend.core.ai_providers import ...`
- [ ] No remaining `import ai_analytics` or `import ai_providers` references exist at root scope anywhere in the codebase
- [ ] `dashboard.py` still boots and renders correctly after the import swap
- [ ] No regression in AI ratings, provider connection tests, or analytics endpoints

---

## Priority Reasoning

**High.** The root `ai_analytics.py` is actively used by `dashboard.py` but returns a **0–100 score scale** while the backend version returns **0–10**. Any shared data or UI comparing ratings from both paths will be silently wrong. It also lacks the yfinance fallback and DB caching that the canonical version has — meaning dashboard users get less resilient, uncached results. This is a correctness bug masquerading as a cleanup task.

---

## Complexity: 2 / 5

`ai_providers.py` is identical — pure deletion + 2 import fixes. `ai_analytics.py` requires verifying `dashboard.py` callers handle the new 0–10 scale correctly, but the import changes themselves are mechanical. Low risk, contained blast radius.
