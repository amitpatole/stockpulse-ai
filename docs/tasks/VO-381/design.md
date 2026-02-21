# VO-381: API Rate Limit Indicator in Data Provider Status

## Technical Design Spec

---

### 1. Approach

Instrument each provider's `DataProvider` subclass to increment an in-memory per-minute call counter inside `DataProviderRegistry`; this avoids touching any provider's HTTP layer or parsing non-standard headers. A new `/api/providers/rate-limits` endpoint reads the registry's live counters and the static `rate_limit_per_minute` ceiling from each `ProviderInfo`, computing usage percentage and rolling-window reset time. The frontend polls this endpoint every 30 s via the existing `useApi` hook and renders a panel in the dashboard with color-coded progress bars per provider.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/data_providers/base.py` — add `record_call(provider_name)` and `get_rate_limit_state()` methods to `DataProviderRegistry`; call `record_call()` from the registry's `get_quote()` / `get_historical()` dispatch path
- **CREATE**: `backend/api/providers.py` — `providers_bp` blueprint with `GET /api/providers/rate-limits`
- **MODIFY**: `backend/app.py` — register `providers_bp`
- **MODIFY**: `frontend/src/lib/types.ts` — add `ProviderRateLimit` and `ProviderRateLimitsResponse` types
- **MODIFY**: `frontend/src/lib/api.ts` — add `getProviderRateLimits()` function
- **CREATE**: `frontend/src/components/dashboard/ProviderRateLimitPanel.tsx` — new dashboard panel component
- **MODIFY**: `frontend/src/app/page.tsx` — import and render `ProviderRateLimitPanel`

---

### 3. Data Model

No new tables. Rate limit state is tracked entirely in memory inside `DataProviderRegistry` using a dict keyed by provider name:

```python
# Added to DataProviderRegistry.__init__
self._call_log: dict[str, list[float]] = {}  # provider_name -> list of epoch timestamps
self._rate_lock = threading.Lock()
```

Existing `data_providers_config.rate_limit_remaining` column is left in place but not used by this feature (it was always -1 in practice).

---

### 4. API Spec

**`GET /api/providers/rate-limits`**

No request body. Returns:

```json
{
  "providers": [
    {
      "name": "polygon",
      "display_name": "Polygon.io",
      "requests_used": 3,
      "requests_limit": 5,
      "window_seconds": 60,
      "reset_at": "2026-02-21T10:31:00Z",
      "pct_used": 60.0,
      "status": "ok"
    }
  ],
  "polled_at": "2026-02-21T10:30:05Z"
}
```

`status` values: `"ok"` (<70%), `"warning"` (70–90%), `"critical"` (>90%), `"unknown"` (limit is 0 or unset).

`reset_at` is the timestamp when the oldest call in the rolling 60-second window expires. If `requests_used` is 0, `reset_at` is `null`.

HTTP 200 always; errors return `{"error": "..."}` with appropriate 5xx code.

---

### 5. Frontend Component Spec

**Component**: `ProviderRateLimitPanel`
**File**: `frontend/src/components/dashboard/ProviderRateLimitPanel.tsx`

**Data fields displayed** (from API response):

| UI Element | API Field |
|---|---|
| Provider name | `display_name` |
| "X / Y req/min" label | `requests_used` / `requests_limit` |
| Progress bar fill % | `pct_used` |
| Progress bar color | `status` → green / yellow / red / gray |
| Reset countdown | `reset_at` → `"Resets in Xm Ys"` or `"—"` |
| "Limit unknown" badge | `status === "unknown"` |

**Renders in**: `frontend/src/app/page.tsx` — added below the existing `KPICards` row in the dashboard grid.

**Layout**: Vertical list of provider rows inside a card container. Each row: provider name on the left, `X / Y` count + colored progress bar in the center, reset countdown right-aligned.

**Loading state**: Skeleton bars (same width as progress bar) shown while `loading === true`.

**Error state**: Single muted line — "Provider status unavailable" — shown when `error` is set.

**Polling**: `useApi<ProviderRateLimitsResponse>('/api/providers/rate-limits', { refreshInterval: 30000 })` — no additional hook needed.

---

### 6. Verification

1. **Counter increments correctly**: Load a stock quote from the dashboard, then call `GET /api/providers/rate-limits` directly — the primary provider's `requests_used` should be ≥ 1 and `pct_used` should be non-zero.

2. **Color thresholds render**: Use the browser dev tools to temporarily override the API response with `pct_used: 75` and verify the progress bar turns yellow; override to `95` and confirm it turns red.

3. **Unknown provider graceful degradation**: Manually add a provider entry with `rate_limit_per_minute: 0` in `__init__.py`, reload the panel — that row should show the "Limit unknown" gray badge instead of a progress bar.
