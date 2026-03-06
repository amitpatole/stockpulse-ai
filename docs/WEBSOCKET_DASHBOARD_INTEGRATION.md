# WebSocket Dashboard Integration Guide

## Overview

This guide shows how to integrate real-time WebSocket price updates with the TickerPulse dashboard components, replacing or complementing the current polling-based approach.

## Current Architecture

The dashboard currently uses polling via the `useApi` hook:

```typescript
// Current: Polling every 30 seconds
const { data: ratings } = useApi<AIRating[]>(getRatings, [], {
  refreshInterval: 30000,
});
```

## WebSocket Integration Options

### Option 1: Event-Driven Real-Time Updates (Recommended)

Replace polling with WebSocket for immediate price updates:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { AIRating } from '@/lib/types';
import StockCard from './StockCard';

export default function StockGridRealTime() {
  const [ratings, setRatings] = useState<AIRating[]>([]);

  // WebSocket with event-driven mode (0ms = immediate delivery)
  const { subscribe, connected, error } = useWebSocket({
    refreshInterval: 0,  // Event-driven, not batched
    autoConnect: true,
    onPriceUpdate: (data) => {
      // Update the rating for this ticker
      setRatings((prev) =>
        prev.map((r) =>
          r.ticker === data.ticker
            ? {
                ...r,
                current_price: data.price,
                price_change_pct: data.change_pct,
              }
            : r
        )
      );
    },
    onConnect: () => {
      console.log('WebSocket connected');
      // On reconnect, re-subscribe to all tickers
      ratings.forEach((r) => subscribe(r.ticker));
    },
  });

  // On mount, fetch initial data and subscribe
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const data = await fetch('/api/ai/ratings').then((r) => r.json());
        setRatings(data);

        // Subscribe to all tickers
        if (connected) {
          data.forEach((r: AIRating) => subscribe(r.ticker));
        }
      } catch (err) {
        console.error('Failed to fetch initial ratings:', err);
      }
    };

    fetchInitial();
  }, [connected, subscribe]);

  if (error) return <div>WebSocket error: {error}</div>;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {ratings.map((rating) => (
        <StockCard key={rating.ticker} rating={rating} />
      ))}
    </div>
  );
}
```

### Option 2: Batched Updates with Configurable Intervals

Reduce network load with batched updates:

```typescript
// Batched mode: deliver updates every 1 second
const { subscribe, connected } = useWebSocket({
  refreshInterval: 1000,  // Batch every 1 second
  onPriceUpdate: (data) => {
    // Handle batched price updates
    updateRating(data.ticker, data);
  },
});
```

### Option 3: Hybrid Approach (Polling + WebSocket)

Use WebSocket when available, fallback to polling:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useApi } from '@/hooks/useApi';
import type { AIRating } from '@/lib/types';

export default function StockGridHybrid() {
  // Polling fallback
  const { data: polledRatings } = useApi<AIRating[]>(
    getRatings,
    [],
    { refreshInterval: 30000 }
  );

  // WebSocket primary
  const [wsRatings, setWsRatings] = useState<AIRating[]>(polledRatings || []);
  const { subscribe, connected, subscriptions } = useWebSocket({
    refreshInterval: 0,
    enableFallback: true,  // Auto-fallback if WS fails
    onPriceUpdate: (data) => {
      setWsRatings((prev) =>
        prev.map((r) =>
          r.ticker === data.ticker
            ? { ...r, current_price: data.price, price_change_pct: data.change_pct }
            : r
        )
      );
    },
  });

  // Use WebSocket data if connected, otherwise use polled data
  const ratings = connected ? wsRatings : polledRatings;

  useEffect(() => {
    // Subscribe to active tickers when connected
    if (connected && wsRatings.length > 0) {
      wsRatings.forEach((r) => {
        if (!subscriptions.includes(r.ticker)) {
          subscribe(r.ticker);
        }
      });
    }
  }, [connected, wsRatings, subscriptions, subscribe]);

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div className="text-xs text-gray-400 col-span-full">
        {connected ? '🟢 Real-time WebSocket' : '🔵 Polling fallback (30s)'}
      </div>
      {ratings?.map((rating) => (
        <StockCard key={rating.ticker} rating={rating} />
      ))}
    </div>
  );
}
```

## Configuring Refresh Intervals

### Via React Hook

```typescript
const { subscribe } = useWebSocket({
  refreshInterval: 1000,  // 1 second batching
  onPriceUpdate: handlePriceUpdate,
});
```

### Via Backend Configuration

```bash
# Set default refresh interval for all WebSocket clients
export WEBSOCKET_DEFAULT_REFRESH_INTERVAL=1000
```

### Via REST API

```bash
# Get current WebSocket settings
curl http://localhost:5000/api/settings/websocket

# Update refresh interval
curl -X POST http://localhost:5000/api/settings/websocket/refresh-interval \
  -H "Content-Type: application/json" \
  -d '{"refresh_interval": 1000}'
```

## Refresh Interval Modes

| Mode | Interval | Use Case | Latency | Throughput |
|------|----------|----------|---------|-----------|
| Event-Driven | 0ms | Active trading, real-time dashboards | <500ms | Highest |
| Fast Batch | 500ms | Responsive monitoring | ~600ms | High |
| Standard Batch | 1000ms | General dashboards | ~1500ms | Medium |
| Slow Batch | 2000-5000ms | Summary views, low-traffic | ~5500ms | Low |

## Performance Considerations

### Benefits of WebSocket Real-Time

- **Latency**: <500ms vs 30s polling
- **Efficiency**: Server pushes only when price changes
- **Scalability**: Reduces polling load on server
- **User Experience**: Immediate price updates

### Network Impact

```
Polling (30s interval):
- 120 requests/hour per client
- 1200 requests/hour for 10 concurrent users

WebSocket (event-driven):
- ~10-50 updates/hour per ticker (during trading)
- Significantly reduced network traffic
- Persistent connection overhead (~100 bytes/minute)
```

## Migration Guide

### Step 1: Add useWebSocket Hook

The hook is already created at `frontend/src/hooks/useWebSocket.ts`

### Step 2: Update Component

Replace `useApi` polling with WebSocket:

```typescript
// Before
const { data: ratings } = useApi(getRatings, [], {
  refreshInterval: 30000,
});

// After
const { subscribe, connected } = useWebSocket({
  refreshInterval: 0,
  onPriceUpdate: (data) => updateRating(data),
});
```

### Step 3: Subscribe to Tickers

```typescript
useEffect(() => {
  if (connected && ratings.length > 0) {
    ratings.forEach((r) => subscribe(r.ticker));
  }
}, [connected, ratings, subscribe]);
```

### Step 4: Handle Fallback

```typescript
const { fallbackMode, error } = useWebSocket({
  enableFallback: true,  // Enable polling fallback
  onDisconnect: () => {
    console.log('WebSocket disconnected, falling back to polling');
  },
});
```

## Dashboard Integration Checklist

- [ ] Create WebSocket instance on dashboard page
- [ ] Subscribe to watched tickers on component mount
- [ ] Update component state on price updates
- [ ] Handle WebSocket disconnection gracefully
- [ ] Display connection status indicator (optional)
- [ ] Update KPICards with real-time data
- [ ] Update NewsFeed refresh with WebSocket timing
- [ ] Test with multiple concurrent subscriptions
- [ ] Test failover to polling
- [ ] Monitor WebSocket connection metrics

## Backend Configuration

```bash
# Enable WebSocket with 1-second batching
WEBSOCKET_DEFAULT_REFRESH_INTERVAL=1000
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_AUTO_RECONNECT=true
WEBSOCKET_ENABLE_POLLING_FALLBACK=true
```

## Monitoring

Check WebSocket health:

```bash
curl http://localhost:5000/api/settings/websocket/health
```

Get WebSocket statistics:

```bash
curl http://localhost:5000/api/settings/websocket
```

## Troubleshooting

### WebSocket Connection Fails

1. Check CORS configuration in `Config.CORS_ORIGINS`
2. Verify SocketIO is initialized: Check logs for "SocketIO initialised"
3. Check browser console for connection errors
4. Fallback to polling should activate automatically

### Missing Price Updates

1. Verify client is subscribed: Check `subscriptions` state
2. Check backend price update job is running
3. Monitor WebSocket logs for broadcast errors

### High Memory Usage

1. Reduce number of concurrent subscriptions
2. Increase refresh interval (e.g., 2000ms instead of 0ms)
3. Check for connection leaks on page navigation

## API Reference

### useWebSocket Hook

```typescript
const {
  connected,           // boolean: WebSocket connected
  connecting,          // boolean: Connection in progress
  subscriptions,       // string[]: Current ticker subscriptions
  refreshInterval,     // number: Current refresh interval (ms)
  error,              // string | null: Connection error
  fallbackMode,       // boolean: Using polling fallback

  connect,            // async (): Connect to server
  disconnect,         // (): Disconnect from server
  subscribe,          // (ticker: string): Subscribe to ticker
  unsubscribe,        // (ticker: string): Unsubscribe from ticker
  updateRefreshInterval, // (interval: number): Change batching interval
} = useWebSocket(config);
```

### Configuration Options

```typescript
interface UseWebSocketConfig {
  refreshInterval?: number;      // 0=event-driven, >0=batch (ms)
  enableFallback?: boolean;       // Enable REST polling fallback
  autoConnect?: boolean;          // Auto-connect on mount
  onConnect?: () => void;         // Connection established callback
  onDisconnect?: (reason) => void; // Disconnection callback
  onPriceUpdate?: (data) => void; // Price update callback
  onSubscribed?: (ticker) => void; // Subscription confirmed callback
  onUnsubscribed?: (ticker) => void; // Unsubscription confirmed callback
  onSubscriptionError?: (ticker, error) => void; // Subscription error callback
}
```

## See Also

- [WebSocket Architecture](07-websocket-price-streaming.md)
- [API Settings Endpoints](../backend/api/settings.py)
- [useWebSocket Hook](../frontend/src/hooks/useWebSocket.ts)
