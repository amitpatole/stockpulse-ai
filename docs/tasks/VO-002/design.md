# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## Technical Design

## Technical Design Spec: Remove Root-Level Duplicate AI Module Files

---

### Approach

Mechanical deletion of two shadowing modules followed by targeted import rewrites. No logic changes required — the canonical `backend/core/` versions already contain the correct, complete implementations. The work is: delete roots, fix imports in consumers, fix one internal cross-reference in the canonical module.

---

### Files to Modify/Create

**Delete:**
- `./ai_analytics.py` (493 lines — diverged, missing fallback logic)
- `./ai_providers.py` (302 lines — duplicate)

**Modify:**
- `dashboard.py` — five inline import statements to rewrite:
  - Lines 240, 249, 259, 388: `from ai_analytics import StockAnalytics` → `from backend.core.ai_analytics import StockAnalytics`
  - Line 361: `from ai_providers import test_provider_connection` → `from backend.core.ai_providers import test_provider_connection`
  - Line 387: `from ai_providers import AIProviderFactory` → `from backend.core.ai_providers import AIProviderFactory`

- `backend/core/ai_analytics.py:465` — fix ambiguous cross-module import:
  - `from ai_providers import AIProviderFactory` → `from .ai_providers import AIProviderFactory`
  - Same line or nearby: `from settings_manager import get_active_ai_provider` → `from .settings_manager import get_active_ai_provider` (verify this import exists and follow the same relative pattern for consistency)

---

### Data Model Changes

None.

---

### API Changes

None. `dashboard.py` endpoints remain identical; only the import resolution path changes.

---

### Frontend Changes

None.

---

### Testing Strategy

**Verification grep (must return zero hits):**
```bash
grep -rn "from ai_analytics\|from ai_providers" . \
  --include="*.py" \
  --exclude-dir=".git"
```

**Run existing test suite:**
```bash
python -m pytest test_import_refactor.py -v
```
`test_import_refactor.py` already contains `TestBackendCoreImports` and `TestImportPathConsistency` classes that assert `backend.core` imports succeed and root-level imports raise `ImportError` — these tests should go green after deletion.

**Smoke check for `dashboard.py` consumers:**
```bash
python -c "import dashboard"
```
Confirms all six rewritten imports resolve without error at module load time.

**Risk:** `backend/core/ai_analytics.py` line 465 currently uses bare `from ai_providers import` — if the root file is deleted before this is fixed to a relative import, the canonical module itself breaks. **Fix the relative import first, delete the root files second.**
