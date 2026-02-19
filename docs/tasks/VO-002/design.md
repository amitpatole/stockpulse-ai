# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## Technical Design

## Technical Design Spec: Remove Root-Level Duplicate Modules

### Approach

Pure deletion + import path correction. No logic changes. Three discrete steps: delete the two root files, fix the 5 lazy imports in `dashboard.py`, and fix the one bare import in `backend/core/ai_analytics.py`. The canonical `backend/core/` versions are the only surviving source of truth.

---

### Files to Modify/Create

**Delete:**
- `/ai_analytics.py` — 493 lines, hardcoded `DB_PATH`, missing fallback logic, missing DB caching
- `/ai_providers.py` — 302 lines, functionally identical to backend/core version (no logic loss on deletion)

**Modify:**

| File | Line(s) | Change |
|------|---------|--------|
| `dashboard.py` | 240, 249, 259 | `from ai_analytics import StockAnalytics` → `from backend.core.ai_analytics import StockAnalytics` |
| `dashboard.py` | 361 | `from ai_providers import test_provider_connection` → `from backend.core.ai_providers import test_provider_connection` |
| `dashboard.py` | 387–388 | `from ai_providers import AIProviderFactory` → `from backend.core.ai_providers import AIProviderFactory` |
| `backend/core/ai_analytics.py` | 465 | `from ai_providers import AIProviderFactory` → `from backend.core.ai_providers import AIProviderFactory` |

All `dashboard.py` imports are lazy (inside route handlers), so no module-level import order issues.

---

### Data Model Changes

None.

---

### API Changes

None. Behavior improves silently: `dashboard.py` routes that previously hit the degraded root module (hardcoded DB path, no caching, wrong score scales) will now use the canonical version with `Config.DB_PATH`, `_save_rating_to_db()`, and correct 0–10/0–1 score normalization.

---

### Frontend Changes

None. The score format difference (0–100 in root vs. 0–10 in canonical) means the canonical version is what the frontend already expects — routes in `backend/api/analysis.py` and `backend/api/chat.py` already import from `backend.core`, so the frontend is calibrated to that output. The `dashboard.py` fix brings it into alignment.

---

### Testing Strategy

1. **Run `test_import_refactor.py`** — the acceptance gate. `test_no_root_level_ai_analytics_import` and `test_no_root_level_ai_providers_import` must pass (they raise `ImportError` on the deleted files). All `backend.core` import smoke tests must pass.

2. **App boot check** — start `dashboard.py` and verify no `ImportError` on startup. Since imports are lazy, exercise each affected route:
   - `GET /api/stock-ratings` (hits `StockAnalytics`)
   - `POST /api/test-provider` (hits `test_provider_connection`)
   - `POST /api/chat` (hits `AIProviderFactory` + `StockAnalytics`)

3. **Existing test suite** — run full test suite to confirm no regressions. No new tests required; `test_import_refactor.py` already encodes the correct end state.
