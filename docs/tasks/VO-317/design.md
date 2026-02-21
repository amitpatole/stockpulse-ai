# VO-317: Create API rate limit indicator in data provider status

## Technical Design

Here's the design spec for VO-380:

---

### 1. Approach

Add a `RateLimitTracker` mixin to the base `DataProvider` class that hooks into each provider's `_get()` method, maintains a per-minute rolling counter in memory, and flushes state to the existing `data_providers_config` table. A new `GET /api/providers/status` endpoint exposes that data. The frontend loads it on mount and subscribes to a new `rate_limit_update` SSE event — fired only at the 70/90/100% thresholds — so the panel stays live without hammering the backend.

---

### 2. Files to Create/Modify

- MODIFY: `backend/data_providers/base.py` — `RateLimitTracker` mixin with `_track_request()` hook
- MODIFY: `backend/data_providers/alpha_vantage_provider.py`, `polygon_provider.py`, `yfinance_provider.py`, `finnhub_provider.py` — call `self._track_request()` inside each `_get()`
- MODIFY: `backend/database.py` — migration to add `rate_limit_used`, `rate_limit_max`, `reset_at` columns to `data_providers_config`
- CREATE: `backend/api/providers.py` — `GET /api/providers/status` blueprint
- MODIFY: `backend/app.py` — register `providers_bp`; add `rate_limit_update` to SSE allowlist
- CREATE: `frontend/src/components/settings/ProviderRateLimitRow.tsx` — per-provider row with progress bar
- MODIFY: `frontend/src/app/settings/page.tsx` — render `ProviderRateLimitRow` in System Status section
- MODIFY: `frontend/src/lib/api.ts` — add `getProviderStatus()`
- MODIFY: `frontend/src/lib/types.ts` — add `ProviderStatus` type

---

### 3. Data Model

No new tables. Three columns added via migration to the existing `data_providers_config` table:

```sql
ALTER TABLE data_providers_config ADD COLUMN rate_limit_used  INTEGER DEFAULT 0;
ALTER TABLE data_providers_config ADD COLUMN rate_limit_max   INTEGER DEFAULT -1;
ALTER TABLE data_providers_config ADD COLUMN reset_at         TIMESTAMP;
```

`rate_limit_max` is seeded from each provider's known tier at startup (Alpha Vantage: 5/min free, Finnhub: 60/min, Yahoo Finance: 120/min, Polygon: 5/min free). `-1` means unknown/unlimited. Note: the existing `rate_limit_remaining` column is superseded by `rate_limit_used` + `rate_limit_max`.

---

### 4. API Spec

**`GET /api/providers/status`** — `200 OK`
```json
{
  "providers": [
    {
      "id": "yahoo_finance",
      "display_name": "Yahoo Finance",
      "is_active": true,
      "rate_limit_used": 42,
      "rate_limit_max": 120,
      "reset_at": "2026-02-21T14:01:00Z"
    }
  ]
}
```

**SSE event `rate_limit_update`** (fires at 70%, 90%, 100% crossings and on reset):
```json
{
  "provider_id": "alpha_vantage",
  "rate_limit_used": 5,
  "rate_limit_max": 5,
  "reset_at": "2026-02-21T14:02:00Z"
}
```

---

### 5. Frontend Component Spec

**Component**: `ProviderRateLimitRow` — `frontend/src/components/settings/ProviderRateLimitRow.tsx`

| UI element | Source field |
|---|---|
| Provider name | `display_name` |
| Usage label `"42 / 120 req/min"` | `rate_limit_used` / `rate_limit_max` |
| Progress bar fill | `rate_limit_used / rate_limit_max × 100` |
| Bar color | green < 70%, yellow 70–90%, red > 90% |
| `"Rate Limited"` badge + reset countdown | shown when `rate_limit_used >= rate_limit_max` |

**Renders in**: `frontend/src/app/settings/page.tsx` — replaces the static yfinance row in the System Status section.

**Loading**: skeleton rows. **Error**: grey `"Unavailable"` text, non-blocking. **SSE**: `useEffect` on the existing `/api/stream` EventSource; merges `rate_limit_update` payload into local state by `provider_id`.

---

### 6. Verification

1. **Threshold color changes**: With Alpha Vantage (5 req/min free), fire 4 rapid requests — bar steps green → yellow → red, badge shows `"Rate Limited"` with countdown.
2. **SSE live update**: Open Settings, trigger requests from another tab — bar advances without page refresh.
3. **Reset recovery**: After the 60-second window rolls, `rate_limit_used` resets to `0`, bar returns green, badge disappears.
