# VO-024: Stale cache in auth flow shows outdated data

## Technical Design

Now I have a thorough understanding. Here is the technical design spec:

---

## Technical Design Spec: Stale Cache in Auth Flow

**Ticket:** Stale cache in auth flow shows outdated data
**Author:** Diana Torres, Architect

---

### Root Cause

Two distinct stale-data paths exist:

1. **Backend — agent engine reads API keys from env vars, not DB.** `crewai_engine.py:_build_crewai_llm` (line 75-80) pulls API keys from `Config` (startup-time env vars). When a user saves a new key via `POST /api/settings/ai-provider`, it is persisted to the `ai_providers` table but **never picked up by the running agent engine**. The `_registry` singleton (created once in `agents/__init__.py:get_registry`) holds stale `AgentConfig` objects for the lifetime of the process.

2. **Frontend — uncontrolled inputs prevent re-render after provider update.** `settings/page.tsx:ProviderCard` uses `defaultValue` on the API key input (line 95) and the model selector (line 113). React only applies `defaultValue` on mount; subsequent `provider` prop changes are silently ignored. After a save or activation, no `refetch` is called, so the provider list itself is stale too.

---

### Approach

- On the backend, make agents resolve the active provider from the DB at execution time rather than at construction time, so a provider switch takes effect on the next agent run with zero process restart.
- On the frontend, convert `ProviderCard` inputs to controlled components keyed on `provider.name`, add save/activate handlers that call `refetch` on success, and wire the existing `useApi` `refetch` return value into mutation callbacks.

---

### Files to Modify

| File | Change |
|---|---|
| `backend/agents/crewai_engine.py` | `_build_crewai_llm`: read active provider API key from `settings_manager.get_active_ai_provider()` as primary source; fall back to `Config` env vars |
| `backend/agents/openclaw_engine.py` | Same pattern if it constructs LLM credentials from `Config` |
| `frontend/src/app/settings/page.tsx` | Convert inputs to controlled; add save + activate handlers; call `refetch` after mutations |
| `frontend/src/lib/api.ts` | Add `saveAIProvider` and `activateAIProvider` typed helpers |

No new files needed.

---

### Data Model Changes

None. `ai_providers` table already has `updated_at` and `is_active` columns sufficient for this fix.

---

### API Changes

No new endpoints. Existing `POST /api/settings/ai-provider` and `POST /api/settings/ai-provider/<id>/activate` are correct. The frontend just needs to actually call them and handle the response.

---

### Frontend Changes

- **`ProviderCard`**: Add `onSaved?: () => void` prop. Convert `defaultValue` → `value` + `onChange` state. On save button click, call `saveAIProvider`; on success, call `onSaved()`.
- **`SettingsPage`**: Pass `refetch` from `useApi(getAIProviders)` into each `ProviderCard` as `onSaved`. Add a key-based `activate` button calling `activateAIProvider` then `refetch`.

---

### Testing Strategy

| Scenario | How |
|---|---|
| Save new API key → agents pick it up immediately | Integration: configure provider via `POST`, trigger agent run, assert agent run log shows new provider name |
| Switch active provider → settings page reflects new active state without reload | E2E (Playwright): activate provider B, assert provider B card shows "active" badge without page refresh |
| Stale `defaultValue` regression | Component test (React Testing Library): mount `ProviderCard` with provider A props, re-render with provider B props, assert input value updates |
| No latency regression | Benchmark agent cold-start before/after: DB lookup for active provider adds one SQLite read (~0.1ms), acceptable |
| Old session does not bleed into new configuration | QA manual: set provider A, restart browser, set provider B, run agent — assert B is used |
