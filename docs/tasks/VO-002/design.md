# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## Technical Design

## Technical Design Spec: Remove Root-Level AI Module Duplicates

---

### Approach

Mechanical deletion + import path surgery. The root `ai_providers.py` is byte-identical to `backend/core/ai_providers.py` — pure deletion. The root `ai_analytics.py` diverges on output scale (0–100 vs 0–10), so after redirecting `dashboard.py` imports to `backend/core/`, we verify each call site handles the canonical return schema correctly. One hidden dependency: `backend/core/ai_analytics.py` itself also imports from root-level `ai_providers` (lines 393, 464) — that must be fixed in the same pass.

---

### Files to Modify/Create

| Action | File |
|--------|------|
| **Delete** | `/ai_analytics.py` |
| **Delete** | `/ai_providers.py` |
| **Update imports** | `dashboard.py` — 6 import statements (lines 240, 249, 259, 361, 387, 388) |
| **Update imports** | `backend/core/ai_analytics.py` — 2 internal imports (lines ~393, ~464): `from ai_providers import` → `from backend.core.ai_providers import` |

No new files created.

---

### Data Model Changes

None. `backend/core/ai_analytics.py` already has `_save_rating_to_db()` using the existing DB schema. No migrations required.

---

### API Changes

No new endpoints. The existing endpoints in `dashboard.py` (`/api/ai-ratings`, `/api/ai-rating/<ticker>`, `/api/chat`, `/api/test-ai-provider`) remain structurally unchanged. **Critical:** the response payload for `/api/ai-ratings` and `/api/ai-rating/<ticker>` will change field semantics:

| Field | Root (old) | backend/core (new) |
|-------|------------|-------------------|
| `score` | 0–100 | 0–10 |
| `confidence` | 0–100 | 0–1 |
| `sentiment_score` | 0–100 | –1 to 1 |

Confirm the frontend already expects 0–10 scale (it should, since `backend/core/` is the canonical version). If the frontend was built against the root version, display values will drop by 10×.

---

### Frontend Changes

Audit the React/JS components consuming `score`, `confidence`, and `sentiment_score` from the ratings endpoints. Verify they render 0–10 scale (e.g., displaying `7.4 / 10` not `74 / 100`). No component rewrites expected — this is a confirmation step only.

---

### Testing Strategy

1. **Smoke test** — start `dashboard.py`, hit `/api/ai-ratings` and `/api/ai-rating/AAPL`; confirm `score` values are in 0–10 range
2. **Provider test** — hit `/api/test-ai-provider`; confirm `test_provider_connection` resolves from `backend.core.ai_providers`
3. **Chat endpoint** — send a message to `/api/chat`; confirm `AIProviderFactory` + `StockAnalytics` both instantiate from `backend.core`
4. **Import audit** — `grep -r "from ai_analytics\|from ai_providers\|import ai_analytics\|import ai_providers" .` returns zero matches after deletion
5. **No circular imports** — verify `backend/core/ai_analytics.py` no longer imports from project root

---

**Blast radius: contained.** Two file deletions, eight import lines changed across two files. No DB migrations, no new API surface, no frontend rewrites required.
