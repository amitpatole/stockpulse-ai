# VO-002: Delete root-level duplicate ai_analytics.py and ai_providers.py

## Technical Design

## Technical Design Spec: Remove Root-Level Duplicate ai_analytics.py and ai_providers.py

### Approach

Delete the two root-level shadow files and update the single consumer (`dashboard.py`) to import from the canonical `backend.core` versions. One internal import inside `backend/core/ai_analytics.py` also needs fixing. The key risk is the **output format divergence**: the root `ai_analytics.py` returns scores on a 0–100 scale; the `backend.core` version returns 0–10 (score) and 0–1 (confidence). `dashboard.py` endpoints that relay these values to the frontend must be audited for scale compatibility.

---

### Files to Modify/Create

**Modify:**
- `dashboard.py` — Replace `from ai_analytics import StockAnalytics` and `from ai_providers import test_provider_connection, AIProviderFactory` with `backend.core` equivalents. Audit the four affected endpoints (`/api/ai/ratings`, `/api/ai/rating/<ticker>`, `/api/chart/<ticker>`, `/api/chat/ask`, `/api/settings/test-ai`) for any score normalization that assumes the 0–100 scale; adjust to match the 0–10 / 0–1 output the canonical version produces.
- `backend/core/ai_analytics.py` — Line 394: change the internal lazy import from `from ai_providers import AIProviderFactory` to `from backend.core.ai_providers import AIProviderFactory`.

**Delete:**
- `ai_analytics.py` (root)
- `ai_providers.py` (root)

**No new files needed.**

---

### Data Model Changes

None. `backend/core/ai_analytics.py` already writes to the `ai_ratings` table; no schema changes required.

---

### API Changes

No endpoint signatures change. Internal behavior improves: responses from `/api/ai/ratings` and `/api/ai/rating/<ticker>` will gain the `price_change`, `price_change_pct`, and `sentiment_label` fields that the canonical version produces, and ratings will now be cached to DB. Verify the frontend handles or ignores the new fields gracefully.

---

### Frontend Changes

None expected, provided `dashboard.py` normalizes the score back to 0–100 **or** the frontend already consumes the 0–10 scale (need to confirm during implementation). No component, route, or state changes.

---

### Testing Strategy

1. **Smoke test** — Start the app; confirm `/api/ai/ratings` and `/api/settings/test-ai` return 200 with valid data.
2. **Import verification** — `python -c "from backend.core.ai_analytics import StockAnalytics; from backend.core.ai_providers import AIProviderFactory"` passes with no `ModuleNotFoundError`.
3. **Scale regression** — Compare a sample rating response before and after; confirm `score` values render correctly in the frontend ratings table (no values showing as `0.x` where integers were expected, or vice versa).
4. **Deletion check** — Confirm `ai_analytics.py` and `ai_providers.py` no longer exist at root; `grep -r "from ai_analytics\|from ai_providers" .` (excluding `venv/`) returns no hits outside `backend/`.
