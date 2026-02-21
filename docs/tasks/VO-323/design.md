# VO-323: Create API rate limit indicator in data provider status

## Technical Design

Here's the design spec for VO-381:

---

### 1. Approach

Instrument `DataProviderRegistry` with an in-memory rolling-window call counter (no HTTP header parsing, no schema changes). A new `/api/providers/rate-limits` endpoint reads live counters against each provider's static `rate_limit_per_minute` ceiling. The frontend polls every 30 s via the existing `useApi` hook and renders color-coded progress bars per provider in the dashboard.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/data_providers/base.py` — add `record_call()` + `get_rate_limit_state()` to `DataProviderRegistry`
- **CREATE**: `backend/api/providers.py` — `providers_bp` with `GET /api/providers/rate-limits`
- **MODIFY**: `backend/app.py` — register `providers_bp`
- **MODIFY**: `frontend/src/lib/types.ts` — add `ProviderRateLimit`, `ProviderRateLimitsResponse`
- **MODIFY**: `frontend/src/lib/api.ts` — add `getProviderRateLimits()`
- **CREATE**: `frontend/src/components/dashboard/ProviderRateLimitPanel.tsx`
- **MODIFY**: `frontend/src/app/page.tsx` — render `ProviderRateLimitPanel` below `KPICards`

---

### 3. Data Model

No new tables. In-memory only — a `dict[str, list[float]]` (provider → list of call timestamps) behind an `RLock` in `DataProviderRegistry`. The existing `data_providers_config.rate_limit_remaining` column is untouched.

---

### 4. API Spec

`GET /api/providers/rate-limits` → 200:
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

`status`: `"ok"` (<70%) / `"warning"` (70–90%) / `"critical"` (>90%) / `"unknown"` (limit unset).

---

### 5. Frontend Component Spec

**`ProviderRateLimitPanel`** at `frontend/src/components/dashboard/ProviderRateLimitPanel.tsx`

Each provider renders as a row: name | colored progress bar + "X / Y req/min" | reset countdown right-aligned. Colors map directly from `status`. Loading state = skeleton bars; error state = "Provider status unavailable" muted text. Uses `useApi('/api/providers/rate-limits', { refreshInterval: 30000 })` — no new hook needed.

---

### 6. Verification

1. Load a stock quote, then `GET /api/providers/rate-limits` — primary provider's `requests_used` should be ≥ 1.
2. Override API response in devtools with `pct_used: 75` → yellow bar; `pct_used: 95` → red bar.
3. Set a provider's `rate_limit_per_minute: 0` → that row shows "Limit unknown" gray badge instead of a progress bar.
