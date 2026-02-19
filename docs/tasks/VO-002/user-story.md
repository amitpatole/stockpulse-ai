# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## User Story

Good — the root-level duplicates are gone, canonical files live in `backend/core/`. Here's the user story:

---

## User Story: Remove Root-Level Duplicate AI Modules

**As a** backend engineer,  
**I want** the root-level `ai_analytics.py` and `ai_providers.py` deleted and all imports pointed to `backend/core/`,  
**so that** there is a single source of truth for AI logic, eliminating silent bugs from diverged code being silently imported.

---

### Acceptance Criteria

- [ ] Root-level `ai_analytics.py` (493 lines) is deleted — no longer importable from project root
- [ ] Root-level `ai_providers.py` (302 lines) is deleted — no longer importable from project root
- [ ] `grep -r "from ai_analytics"` and `grep -r "import ai_analytics"` at root scope return zero hits
- [ ] Same for `ai_providers` at root scope
- [ ] All existing imports updated to `from backend.core.ai_analytics import ...` / `from backend.core.ai_providers import ...`
- [ ] Application boots without import errors
- [ ] Existing tests pass — no regressions from the diverged fallback logic that was missing in the root version

---

### Priority Reasoning

**High.** This is a latent correctness bug, not just cleanup. The root `ai_analytics.py` is missing fallback logic present in `backend/core/`. Any code importing the root version silently runs an inferior code path. The longer this exists, the more import paths diverge, making the eventual fix more expensive.

---

### Estimated Complexity: **2 / 5**

Mechanical deletion + import search-and-replace. Risk is low given the canonical versions are already the complete implementation. The main surface area is ensuring no wildcard or dynamic imports reference the root files.
