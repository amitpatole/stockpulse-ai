# Technical Design Spec: Configurable Real-Time Price Refresh

## Approach

Extend existing WebSocket infrastructure (`backend/websocket/`, `backend/core/price_streamer.py`) with user-configurable refresh intervals. Store refresh preferences in user settings table with per-ticker granularity. Dashboard subscribes to WebSocket events and applies client-side rate limiting based on user preference (1s, 5s, 10s, 30s, 60s).

**Strategy**:
1. Add `refresh_interval` field to user settings (default: 5s)
2. Store per-ticker overrides in new `ticker_refresh_preferences` table
3. Client sends refresh preference with subscribe event
4. Server respects client preference when broadcasting updates
5. Dashboard listens to WebSocket price updates and renders in real-time

---

## Files to Modify/Create

### Backend
- **`backend/database.py`** (MODIFY)
  - Add `ticker_refresh_preferences` table with columns: `user_id, ticker, interval_seconds, created_at, updated_at`
  - Add indices on `(user_id, ticker)` and `created_at`

- **`backend/core/price_streamer.py`** (MODIFY)
  - Replace hardcoded `update_interval=5` with configurable per-client intervals
  - Add `client_intervals` dict: `client_id -> interval_seconds`
  - Modify `_stream_loop()` to respect per-client intervals using separate timers per subscription

- **`backend/websocket/manager.py`** (MODIFY)
  - Add `set_client_interval()` method to store client's preferred interval
  - Pass interval to broadcast handler
  - Add `get_subscribed_clients_by_interval()` to batch clients by interval

- **`backend/websocket/blueprint.py`** (MODIFY)
  - Update subscribe event to accept optional `interval_seconds` parameter
  - Validate interval (1-60s range)
  - Call `manager.set_client_interval()` on subscribe

- **`backend/core/stock_manager.py`** (or new settings module) (MODIFY)
  - Add `get_user_refresh_preference()` to fetch default + per-ticker overrides
  - Add `set_ticker_refresh_interval()` to update preference

### Frontend
- **`frontend/src/components/dashboard/PriceUpdates.tsx`** (NEW)
  - Subscribe to WebSocket on mount with user's refresh preference
  - Apply client-side debouncing/throttling to respect interval
  - Render real-time price updates in stock cards/tables

- **`frontend/src/hooks/useWebSocket.ts`** (MODIFY)
  - Add `interval_seconds` parameter to `subscribe()` method
  - Send interval with subscribe event payload

- **`frontend/src/components/settings/RefreshSettings.tsx`** (NEW)
  - UI to set default refresh interval (dropdown: 1s, 5s, 10s, 30s, 60s)
  - Per-ticker override option in watchlist/portfolio
  - Call `PATCH /api/settings/refresh-interval` to save preference

### API Endpoints
- **`PATCH /api/settings/refresh-interval`** (NEW)
  - Request: `{ "interval_seconds": 5 }`
  - Response: `{ "data": { "interval_seconds": 5 }, "meta": {} }`

- **`GET /api/settings/refresh-interval`** (NEW)
  - Response: `{ "data": { "default": 5, "overrides": { "AAPL": 1, "MSFT": 10 } }, "meta": {} }`

- **`PATCH /api/stocks/:ticker/refresh-interval`** (NEW)
  - Per-ticker override
  - Request: `{ "interval_seconds": 10 }`

---

## Data Model Changes

**New Table**: `ticker_refresh_preferences`
```sql
CREATE TABLE ticker_refresh_preferences (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  interval_seconds INTEGER NOT NULL CHECK (interval_seconds BETWEEN 1 AND 60),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE(user_id, ticker)
);
```

**Modified**: `user_settings` table
- Add column: `refresh_interval_seconds INTEGER DEFAULT 5`

---

## Frontend Integration

1. **Dashboard**: On load, fetch user's refresh preference
2. **Subscription**: Connect WebSocket with interval in subscribe payload
3. **Real-time Updates**: Listen to `price_update` events, update chart/table
4. **Settings UI**: Allow users to change default interval or override per ticker
5. **Fallback**: If WebSocket unavailable, REST API with user's preferred interval

---

## Testing Strategy

- **Unit Tests**: Interval validation (1-60s), per-client timer logic
- **Integration Tests**: Subscribe with interval, verify broadcast timing
- **E2E Tests**: User sets preference → Dashboard updates with correct interval
- **Performance**: Verify no CPU spike with 1000 clients × 1s interval

---

## Business Rules

- Default interval: 5 seconds
- Valid range: 1-60 seconds
- Per-ticker overrides stored per user (isolated data)
- Override takes precedence over default
- Interval applies per client (not global)
- Broadcast triggered on price change OR interval elapsed (whichever first)

---

**Status**: Ready for development ✅
