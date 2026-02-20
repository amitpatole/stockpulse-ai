# VO-025: Null Reference in Settings Page — Technical Design

## Approach

Two-layer fix: (1) harden the data path from API response through the frontend
so a zero-data user never causes a JS crash, and (2) add an error-state render
path so a fetch failure degrades gracefully rather than leaving the page blank.
No schema changes, no new endpoints.

---

## Root Cause

`useApi` exposes an `error` field, but the settings page destructures only
`data` and `loading`. When the fetch fails or the backend returns a malformed
body, `providers` stays `null` and `error` is silently swallowed. Three
compounding gaps:

1. **`frontend/src/lib/api.ts` — `getAIProviders`**: no guard on the parsed
   JSON. If the backend returns a non-array (e.g. a `{"error": "..."}` 500
   body), the caller receives it as `AIProvider[]`, and any downstream
   `.map()` call throws a runtime null/type error.

2. **`frontend/src/app/settings/page.tsx`**: `error` from both `useApi` calls
   is never captured. A fetch failure produces `providers === null`,
   `loading === false`, `error !== null` — and none of the three conditional
   branches (`loading && !providers`, `providers && (...)`,
   `providers && providers.length === 0`) fire, so the entire AI Providers
   section renders blank with no user feedback.

3. **`backend/api/settings.py` — `get_ai_providers_endpoint`**: the body is
   not wrapped in try/except. If `get_all_ai_providers()` raises despite its
   internal guard (e.g., during a DB migration state), Flask returns a 500
   with an HTML error page, not JSON, which crashes `response.json()` in the
   frontend fetcher.

---

## Files to Modify

| File | Change |
|---|---|
| `frontend/src/lib/api.ts` | Add array guard in `getAIProviders`; add null guard in `getHealth` |
| `frontend/src/app/settings/page.tsx` | Capture `error` from both `useApi` calls; add error-state render for AI Providers section |
| `backend/api/settings.py` | Wrap `get_ai_providers_endpoint` body in try/except; return `[]` on error |
| `backend/tests/test_settings_api.py` | New file — regression tests for zero-data user |

---

## Data Model Changes

None.

---

## API Changes

None. `GET /api/settings/ai-providers` already returns a valid 4-element array
for a zero-data user (all providers marked `configured: false`). The only
change is adding a top-level try/except so a DB exception yields
`jsonify([]), 200` instead of a 500.

---

## Frontend Changes

**`src/lib/api.ts`** — `getAIProviders` return guard:
```ts
const data = await res.json();
return Array.isArray(data) ? data : [];
```

**`src/app/settings/page.tsx`** — capture error and render it:
```tsx
const { data: providers, loading: providersLoading, error: providersError } =
  useApi<AIProvider[]>(getAIProviders, []);
```
Add a third branch in the AI Providers section (after the empty-state check):
```tsx
{!providersLoading && !providers && providersError && (
  <div className="rounded-xl border border-dashed border-slate-700 ...">
    <p className="text-sm text-slate-500">
      Could not load provider configuration.
    </p>
  </div>
)}
```
No visible error detail surfaced to the user — matches AC "silent graceful
degradation."

---

## Testing Strategy

**New file: `backend/tests/test_settings_api.py`**

- `test_ai_providers_zero_data_user` — call `GET /api/settings/ai-providers`
  with a fresh empty SQLite DB; assert HTTP 200 and a 4-element JSON array
  with all providers having `configured: false`.
- `test_ai_providers_returns_array_on_db_error` — mock
  `settings_manager.get_all_ai_providers` to raise `sqlite3.OperationalError`;
  assert the endpoint still returns HTTP 200 with `[]` (not a 500).

Existing pytest fixture pattern from `test_agents_api.py` applies directly
(`create_app()` + `app.test_client()`).

Frontend: no test framework is currently configured. Per the acceptance
criteria, a backend regression test is the non-negotiable deliverable; a
frontend Playwright/Jest smoke test can follow in a separate ticket once the
test harness is set up.
