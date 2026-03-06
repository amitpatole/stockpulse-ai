# Feature: WebSocket Real-Time Price Streaming

## Overview
Real-time price updates delivered to connected clients via WebSocket (SocketIO). Clients subscribe to specific stock tickers and receive live price data with <500ms latency. Supports graceful fallback to REST polling if WebSocket unavailable, with automatic reconnection and exponential backoff.

---

## Data Model

### No new database tables required
Uses existing `stocks` and `prices` tables. WebSocket manages in-memory subscription state only.

### WebSocket Message Format
```json
{
  "type": "price_update",
  "ticker": "AAPL",
  "price": 150.25,
  "change": 2.50,
  "change_pct": 1.69,
  "timestamp": "2026-03-03T14:30:00Z",
  "volume": 45000000
}
```

### Subscription State (In-Memory)
- `client_id -> Set[ticker]`: Track which tickers each client subscribes to
- `ticker -> Set[client_id]`: Reverse mapping for efficient broadcasting
- `max_connections`: 1000 concurrent WebSocket connections

---

## API Endpoints

### WebSocket Namespace: `/prices`

#### Event: `subscribe`
**Direction**: Client → Server
**Payload**:
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```
**Response**: Success with subscribed tickers list
**Errors**: Invalid ticker format, max subscriptions per client exceeded

#### Event: `unsubscribe`
**Direction**: Client → Server
**Payload**:
```json
{
  "tickers": ["AAPL"]
}
```
**Response**: Success with remaining subscriptions

#### Event: `price_update` (broadcast)
**Direction**: Server → Client
**Payload**: See "WebSocket Message Format" above
**Frequency**: On price change (triggered by price update job)

#### HTTP Health Check: `GET /api/websocket/health`
**Response**:
```json
{
  "status": "ok|error",
  "message": "WebSocket server is running"
}
```

---

## Files to Modify/Create

### Backend
- **`backend/websocket/manager.py`** (NEW)
  - `WebSocketManager` class with thread-safe subscription handling
  - Methods: `register_client()`, `unregister_client()`, `subscribe()`, `unsubscribe()`, `broadcast_price()`

- **`backend/websocket/blueprint.py`** (NEW)
  - `create_websocket_blueprint()`: Health check endpoint
  - `register_websocket_events()`: Event handler registration

- **`backend/app.py`** (MODIFY)
  - Initialize SocketIO: `socketio = SocketIO(app, async_mode='threading')`
  - Register WebSocket blueprint and events on app startup

- **`backend/jobs/price_alerts_monitor.py`** (MODIFY)
  - Call `socketio.emit()` to broadcast price updates to subscribed clients

### Frontend
- **`frontend/src/hooks/useWebSocket.ts`** (NEW)
  - Hook managing WebSocket connection lifecycle
  - Methods: `subscribe()`, `unsubscribe()`, `reconnect()`, `disconnect()`
  - Auto-reconnection with exponential backoff (1s → 32s max)
  - Fallback to REST polling if WebSocket unavailable

- **`frontend/src/lib/websocket-client.ts`** (NEW)
  - SocketIO client wrapper with event listeners
  - Price update subscription/unsubscription logic

### Tests
- **`backend/tests/test_websocket_blueprint.py`** (NEW)
  - Blueprint integration tests (auth, routing, error handling)
  - Connection limits, message routing, ticker validation

- **`e2e/websocket-prices.spec.ts`** (NEW)
  - Browser-level WebSocket workflows
  - Subscribe/unsubscribe, UI updates, reconnection

---

## Business Rules

1. **Subscription Limits**: Max 50 tickers per client
2. **Ticker Validation**: Alphanumeric + `.-` only (e.g., AAPL, BRK.A, RELIANCE.NS)
3. **Connection Limits**: Max 1000 concurrent connections
4. **Message Broadcast**: Only to clients subscribed to that ticker
5. **Cleanup**: Auto-unsubscribe on client disconnect
6. **Fallback**: REST polling activated if WebSocket unavailable for >30s
7. **Refresh Interval**:
   - **0ms (Event-Driven)**: Price updates delivered immediately when price changes
   - **>0ms (Batched)**: Updates batched and delivered every N milliseconds
   - Valid presets: 0, 500, 1000, 2000, 5000 milliseconds
   - Configurable per client via `useWebSocket({ refreshInterval: 1000 })`

---

## Edge Cases

- **No subscriptions**: Client connected but no tickers → no messages sent
- **Duplicate subscribe**: Idempotent (no error, no duplicate messages)
- **Unsubscribe non-existent**: Idempotent (no error)
- **Network partition**: Exponential backoff reconnection (1s, 2s, 4s, 8s, 16s, 32s)
- **Price update before client subscribe**: Buffered (only sent to new subscribers)
- **Client bulk subscribe**: Validated server-side before partial subscription

---

## Security

- **Authentication**: Validated via session/JWT (future: implement cookie-based auth)
- **Ticker Validation**: Server-side whitelist + regex pattern matching
- **Rate Limiting**: Connection-level via max_connections, message-level per ticker
- **Input Sanitization**: Tickers uppercased, special chars rejected
- **Namespace Isolation**: `/prices` namespace isolated from other SocketIO namespaces

---

## Testing Strategy

### Unit Tests
- `WebSocketManager`: 30+ tests covering subscription state, concurrency, ticker validation
- Happy path: subscribe, unsubscribe, broadcast
- Error handling: invalid ticker, max connections exceeded, client not found
- Edge cases: duplicate subscribe, race conditions, cleanup on disconnect

### Integration Tests
- Blueprint health check endpoint
- Event handler registration and routing
- Connection/disconnection lifecycle
- Message format validation
- Error propagation

### E2E Tests
- Browser connects, subscribes to ticker
- Receives price updates in real-time
- Unsubscribe stops updates
- Multiple tickers subscribed independently
- Reconnection on network failure
- Fallback to REST polling

---

## Performance & Reliability

- **Latency**: <500ms end-to-end (SocketIO overhead ~50-100ms)
- **Throughput**: 1000+ concurrent connections, 100+ updates/sec per ticker
- **Memory**: ~500 bytes per subscription (ticker + client_id)
- **Failover**: Graceful downgrade to REST polling with exponential backoff

---

## Monitoring & Alerting

- **Metrics**:
  - Active WebSocket connections
  - Message latency per ticker
  - Subscribe/unsubscribe rate
  - Fallback to polling percentage

- **Alerts**:
  - Connection count >900 (approaching limit)
  - Message latency >1s
  - Fallback rate >10%

---

## Configurable Refresh Intervals

### Overview
Real-time price updates support configurable refresh intervals to balance latency vs. throughput:

### Modes
- **Event-Driven (0ms)**: Immediate delivery on every price change
  - Lowest latency, highest throughput
  - Best for active trading dashboards

- **Batched (500-5000ms)**: Buffer updates, deliver at fixed intervals
  - Reduces network chatter
  - Best for monitoring dashboards
  - Configurable: 500ms, 1s, 2s, 5s

### Usage

**Backend Configuration** (environment variables):
```bash
WEBSOCKET_DEFAULT_REFRESH_INTERVAL=1000      # Default: 0 (event-driven)
WEBSOCKET_MAX_SUBSCRIPTIONS_PER_CLIENT=50
WEBSOCKET_AUTO_RECONNECT=true
WEBSOCKET_ENABLE_POLLING_FALLBACK=true
```

**Frontend Hook Usage**:
```typescript
const { subscribe, connected, subscriptions } = useWebSocket({
  refreshInterval: 1000,  // Batch updates every 1 second
  onPriceUpdate: (data) => console.log(`${data.ticker}: $${data.price}`),
  enableFallback: true,   // Fallback to REST polling
});

// Subscribe to tickers
useEffect(() => {
  if (connected) {
    subscribe('AAPL');
    subscribe('MSFT');
  }
}, [connected, subscribe]);
```

**REST API** (get/set refresh interval):
```bash
# Get current WebSocket settings
curl http://localhost:5000/api/settings/websocket

# Set refresh interval for new connections
curl -X POST http://localhost:5000/api/settings/websocket/refresh-interval \
  -H "Content-Type: application/json" \
  -d '{"refresh_interval": 1000}'
```

## Implementation Timeline

**Phase 1** (COMPLETE): Backend WebSocket manager + blueprint
**Phase 2** (COMPLETE): Frontend hook + client wrapper
**Phase 3** (COMPLETE): Test suite (unit + E2E)
**Phase 4** (COMPLETE): Configurable refresh intervals + REST API
**Phase 5** (PENDING): Monitoring & metrics collection
**Phase 6** (PENDING): Dashboard integration with refresh interval selector

---

## Acceptance Criteria

- ✅ AC1: Subscribe/unsubscribe to specific tickers
- ✅ AC2: Real-time delivery <500ms latency
- ✅ AC3: UI reflects updates immediately
- ✅ AC4: Multiple subscriptions work independently
- ✅ AC5: Unsubscribe stops receiving updates
- ✅ AC6: Graceful fallback to REST polling
- ✅ AC7: Auto-reconnection with exponential backoff
- ✅ AC8: Configurable refresh intervals (0ms = event-driven, >0 = batched updates)

---

## Git History

- **Commit**: `6686ef9` - feat: Implement real-time WebSocket price updates
- **Branches**: `feat/websocket-prices` (merged to main)
- **Code Review**: Required before merge

---

**Status**: Design complete, implementation complete, testing complete ✅
