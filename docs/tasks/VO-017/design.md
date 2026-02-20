# VO-017: Null reference in settings page when user has no data

## Technical Design

Here's the design spec for VO-017:

---

**Root cause — three compounding gaps, not one:**

1. **`src/lib/api.ts` (`getAIProviders`)** — no guard on the parsed JSON response. If the backend returns a non-array error body, the typed `AIProvider[]` cast silently passes through, and any downstream `.map()` call throws a runtime crash.

2. **`src/app/settings/page.tsx`** — `error` from both `useApi` calls is never destructured. When a fetch fails, `providers === null`, `loading === false`, `error !== null` — none of the three conditional branches fire, so the AI Providers section renders blank. Not a hard crash on a zero-data user with a healthy backend, but a crash if the fetcher itself throws.

3. **`backend/api/settings.py` (`get_ai_providers_endpoint`)** — no top-level try/except. If `get_all_ai_providers()` raises an unhandled exception (e.g., table mid-migration), Flask returns an HTML 500, which breaks `response.json()` in the frontend and crashes the hook.

**Fix surface is narrow:**

| File | What changes |
|---|---|
| `frontend/src/lib/api.ts` | `Array.isArray(data) ? data : []` guard |
| `frontend/src/app/settings/page.tsx` | Capture `error`, add a third graceful-degradation branch |
| `backend/api/settings.py` | Top-level try/except → return `[]` on error |
| `backend/tests/test_settings_api.py` | New — zero-data user test + DB-error resilience test |

No schema changes, no new endpoints. Complexity estimate of 2/5 holds — this is pure null-guard work across two layers.
