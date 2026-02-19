# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## User Story

Good — clear picture. Here's the user story.

---

## User Story: Remove Root-Level Duplicate AI Module Files

**As a** backend developer,
**I want** the root-level `ai_analytics.py` and `ai_providers.py` deleted and all imports redirected to `backend/core/`,
**so that** there is a single source of truth for AI logic, eliminating the risk of silent regressions when only one version gets updated.

---

### Acceptance Criteria

- `./ai_analytics.py` (493 lines) is deleted from the repo root
- `./ai_providers.py` (302 lines) is deleted from the repo root
- `dashboard.py` imports are updated:
  - `from ai_analytics import StockAnalytics` → `from backend.core.ai_analytics import StockAnalytics` (lines 240, 249, 259, 388)
  - `from ai_providers import test_provider_connection` → `from backend.core.ai_providers import test_provider_connection` (line 361)
  - `from ai_providers import AIProviderFactory` → `from backend.core.ai_providers import AIProviderFactory` (line 387)
- The self-referencing import in root `ai_analytics.py:394` is gone (file deleted)
- `backend/core/ai_analytics.py:465` internal import of `ai_providers` is updated to a relative import (`from .ai_providers import AIProviderFactory`) so it no longer resolves ambiguously
- No existing tests break after the change
- `grep -r "from ai_analytics\|from ai_providers" .` returns zero root-level hits

---

### Priority Reasoning

**High.** This is a latent correctness bug, not just tidiness. The root `ai_analytics.py` is 71 lines shorter than the canonical version — it's missing fallback logic. Any code path that resolves to the root file silently skips that logic. Python's module resolution makes this timing-dependent and hard to catch in review. The fix is low-risk and high-leverage.

---

### Estimated Complexity: **2 / 5**

Mechanical file deletion + targeted import rewrites across one primary consumer (`dashboard.py`) and one internal cross-reference. No new logic required. Main risk is verifying no other entry points (scripts, notebooks, tests) import from the root — a quick grep confirms the blast radius is small.
