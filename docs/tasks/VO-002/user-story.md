# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## User Story

Good intel. Here's the user story:

---

## User Story: Remove Root-Level Duplicate Core Modules

**As a** backend developer on Virtual Office,
**I want** the root-level `ai_analytics.py` and `ai_providers.py` files removed and all imports pointed to `backend/core/`,
**so that** there is a single canonical source of truth for core AI logic, eliminating the risk of diverged behavior between the legacy standalone path and the production backend.

---

### Acceptance Criteria

- [ ] Root-level `ai_analytics.py` (493 lines) is deleted
- [ ] Root-level `ai_providers.py` (302 lines) is deleted
- [ ] `dashboard.py` imports updated from root-level to `backend.core.ai_analytics` / `backend.core.ai_providers`
- [ ] No remaining `import ai_analytics` or `import ai_providers` without the `backend.core.` prefix anywhere in the codebase
- [ ] All existing backend tests pass after the change
- [ ] App starts without import errors

---

### Priority Reasoning

**High.** The root `ai_analytics.py` is already 71 lines behind the canonical version — it's missing the fallback chain and DB caching logic added in recent sprints. Any developer who accidentally runs or imports the root version will silently get degraded behavior with no error. This is an active maintenance hazard that compounds with every feature added to `backend/core/`.

`ai_providers.py` is currently identical, but that's exactly the window to clean it up — before it drifts too.

---

### Estimated Complexity: **2 / 5**

Surgical deletions + one file (`dashboard.py`) to update. The canonical versions are already complete. No logic changes required — pure import hygiene.
