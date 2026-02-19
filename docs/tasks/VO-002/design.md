# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## Technical Design

Here's the design spec I wrote:

---

## Design Summary

**Approach:** Mechanical deletion with targeted import fixups. The canonical `backend/core/` versions are already the complete implementations — no logic needs to be migrated. The main non-obvious risk is a latent root-level import *inside the canonical file itself*.

**Files to change:**

| File | Action |
|---|---|
| `ai_analytics.py` (root) | Delete |
| `ai_providers.py` (root) | Delete |
| `backend/core/ai_analytics.py:465` | Fix `from ai_providers import AIProviderFactory` → `from backend.core.ai_providers import ...` |
| `dashboard.py` (6 import sites) | Retarget 4× `ai_analytics` + 2× `ai_providers` imports to `backend.core.*` |

**Critical subtlety:** `backend/core/ai_analytics.py` itself has a lazy import on line 465 pointing at the root `ai_providers`. This must be fixed *before* the root files are deleted — otherwise the canonical file silently breaks the first time that code path executes.

**No data model, API, or frontend changes required.**

**Testing:** `test_import_refactor.py` already tests only `backend.core.*` imports (good baseline). Post-deletion: run it, grep for zero remaining root-level import hits, and do a Flask `create_app()` boot check.
