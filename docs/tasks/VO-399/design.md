# VO-399: Screen reader accessibility issue in data provider fallback chain

## Technical Design

## VO-362 Technical Design Spec: Screen Reader Accessibility — Data Provider Fallback Chain

---

### 1. Approach

The backend's `DataProviderRegistry` (`backend/data_providers/base.py`) already fires `provider_fallback` SSE events via the `on_fallback` callback, but emits nothing when the primary recovers — add `_in_fallback` state tracking and a `provider_recovered` SSE event when the primary succeeds after a fallback period. On the frontend, extend `useSSE.ts` to handle both event types with a 2 s debounce guard, feeding the existing `SSEAccessibilityAnnouncer` live regions with polite/assertive copy. A new `ProviderStatusBadge` component surfaces the active fallback visually and accessibly in the dashboard header.

---

### 2. Files to Create/Modify

- MODIFY: `backend/data_providers/base.py` — add `_in_fallback: bool` + `on_recovered` callback to `DataProviderRegistry`; emit recovery event when primary succeeds post-fallback
- MODIFY: `backend/app.py` — add `'provider_recovered'` to `_ALLOWED_EVENT_TYPES`; register `_on_provider_recovered` callback alongside existing `_on_provider_fallback`
- MODIFY: `frontend/src/lib/types.ts` — add `'provider_fallback' | 'provider_recovered'` to `SSEEventType`; add `ProviderFallbackState` interface
- MODIFY: `frontend/src/hooks/useSSE.ts` — handle `provider_fallback` and `provider_recovered` events; 2 s debounce ref; track `fallbackActive` + `fallbackInfo` in state
- CREATE: `frontend/src/components/dashboard/ProviderStatusBadge.tsx` — accessible pill badge for active fallback
- MODIFY: `frontend/src/app/page.tsx` — render `ProviderStatusBadge` in header toolbar

---

### 3. Data Model

No new tables. `_in_fallback: bool` lives in `DataProviderRegistry` memory only (reset on `set_primary()` call).

---

### 4. API Spec

No new HTTP endpoints. Two SSE event types over the existing `/api/stream`:

**`provider_fallback`** (already emitted — shape unchanged):
```json
{ "from_provider": "Polygon", "to_provider": "Yahoo Finance",
  "tier": "free", "reason": "exception", "timestamp": "2026-02-22T10:00:00Z" }
```

**`provider_recovered`** (new):
```json
{ "recovered_provider": "Polygon", "fallback_was": "Yahoo Finance",
  "timestamp": "2026-02-22T10:05:00Z" }
```

---

### 5. Frontend Component Spec

**Component**: `ProviderStatusBadge`
**File**: `frontend/src/components/dashboard/ProviderStatusBadge.tsx`

| Data field | Source | UI element |
|---|---|---|
| `fallbackActive` | `useSSE().fallbackActive` | Badge visibility |
| `fallbackInfo.to_provider` | SSE payload | Badge label text |
| `fallbackInfo.reason` | SSE payload | `aria-label` detail |

**Renders in**: `frontend/src/app/page.tsx`, header toolbar, after the connection status indicator.

**Layout**: Pill badge — warning icon (`aria-hidden="true"`) + text `"Fallback: {to_provider}"`. Full accessible label: `aria-label="Data source: fallback active, using {to_provider} ({reason})"`. `tabIndex={0}` so it is keyboard-reachable. Rendered `null` when `fallbackActive === false`.

**ARIA copy fed to `SSEAccessibilityAnnouncer`**:
- Fallback event → polite: `"Primary data source unavailable. Using fallback provider: {to_provider}."`
- Full unavailability (all providers exhausted) → assertive: `"Market data unavailable. All data providers failed."`
- Recovery event → polite: `"Primary data source restored."`

---

### 6. Verification

1. **Fallback announcement**: Set an invalid API key for the primary provider; trigger a quote request; confirm the screen reader announces `"Primary data source unavailable. Using fallback provider: Yahoo Finance."` within 3 s and `ProviderStatusBadge` appears in the header with the correct `aria-label`.
2. **Recovery announcement**: Restore the primary key and trigger another quote request; confirm the screen reader announces `"Primary data source restored."` and the badge disappears.
3. **Debounce (flap suppression)**: Simulate 5 provider switches within 2 s; confirm via `announce()` call count in unit tests that no more than one ARIA announcement fires per 2 s window.
