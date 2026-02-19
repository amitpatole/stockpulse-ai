# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## Technical Design

## Technical Design Spec: Remove Root-Level Duplicate Core Modules

---

### Approach

Surgical deletion of two root-level files followed by targeted import updates in `dashboard.py` and one fix inside `backend/core/ai_analytics.py` itself. No logic changes — canonical implementations in `backend/core/` are already complete and more capable.

One non-obvious finding: `backend/core/ai_analytics.py:465` contains a dynamic import `from ai_providers import AIProviderFactory` that still references the root-level module. This must be fixed in the same pass or deletion will break the canonical file.

---

### Files to Modify / Delete

| Action | Path | Detail |
|--------|------|--------|
| **Delete** | `ai_analytics.py` | 493 lines, root-level legacy copy |
| **Delete** | `ai_providers.py` | 302 lines, root-level legacy copy |
| **Modify** | `dashboard.py` | 6 dynamic imports to update (lines 240, 249, 259, 388 → `backend.core.ai_analytics`; lines 361, 387 → `backend.core.ai_providers`) |
| **Modify** | `backend/core/ai_analytics.py` | Line 465: fix `from ai_providers import` → `from backend.core.ai_providers import` |

No other files require changes — all other callers already use the `backend.core.*` prefix.

---

### Data Model Changes

None.

---

### API Changes

None. All endpoints already route through `backend/api/` which uses `backend.core.*` imports.

---

### Frontend Changes

None.

---

### Testing Strategy

**Existing coverage to verify:**

- `test_import_refactor.py` already contains tests (lines 57, 62, 379, 382) that assert `import ai_analytics` and `import ai_providers` raise `ImportError`. These will pass naturally once the root files are deleted — confirm they do.
- Run `test_import_refactor.py` in full to confirm all `backend.core.*` smoke imports succeed.
- Run `backend/tests/test_data_provider_fallback.py` — tests the fallback chain in `backend/core/ai_analytics.py`; must still pass.
- Run `backend/tests/test_agents_api.py` — agents use `backend.core.ai_providers`; must still pass.

**Manual smoke check:**

Start the app and hit one AI-dependent endpoint (e.g., `/api/analysis/<ticker>`) to confirm no `ModuleNotFoundError` at runtime from `dashboard.py`'s updated dynamic imports.

**Definition of done:** all existing tests green, app starts, no `import ai_analytics` or `import ai_providers` (bare, without `backend.core.` prefix) remaining in codebase except inside `test_import_refactor.py`'s intentional failure-assertion blocks.
