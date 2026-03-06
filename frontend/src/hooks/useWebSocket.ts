/**
 * useWebSocket - React Hook for real-time WebSocket price updates
 *
 * Features:
 * - Auto-reconnect with exponential backoff (1s → 32s)
 * - Subscribe/unsubscribe to stock tickers
 * - Fallback to REST polling if WebSocket unavailable
 * - Configurable refresh intervals
 * - Connection lifecycle management
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { getWebSocketClient, WebSocketClient, PriceUpdate } from '../lib/ws-client';

export interface UseWebSocketConfig {
  /** Default refresh interval in milliseconds (0 = event-driven) */
  refreshInterval?: number;
  /** Enable automatic fallback to REST polling */
  enableFallback?: boolean;
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Callback when connection established */
  onConnect?: () => void;
  /** Callback when connection lost */
  onDisconnect?: (reason: string) => void;
  /** Callback when price updates received */
  onPriceUpdate?: (data: PriceUpdate) => void;
  /** Callback on subscription confirmation */
  onSubscribed?: (ticker: string) => void;
  /** Callback on unsubscription confirmation */
  onUnsubscribed?: (ticker: string) => void;
  /** Callback on subscription error */
  onSubscriptionError?: (ticker: string, error: string) => void;
}

export interface UseWebSocketState {
  connected: boolean;
  connecting: boolean;
  subscriptions: Set<string>;
  refreshInterval: number;
  error: string | null;
  fallbackMode: boolean;
}

/**
 * React hook for managing WebSocket price updates
 *
 * @param config Configuration options
 * @returns State and methods for WebSocket management
 *
 * @example
 * const { subscribe, unsubscribe, connected, subscriptions } = useWebSocket({
 *   refreshInterval: 1000, // 1 second
 *   onPriceUpdate: (data) => console.log(`${data.ticker}: $${data.price}`),
 * });
 *
 * useEffect(() => {
 *   if (connected) {
 *     subscribe('AAPL');
 *     subscribe('MSFT');
 *   }
 * }, [connected]);
 */
export function useWebSocket(config: UseWebSocketConfig = {}) {
  const {
    refreshInterval = 0, // 0 = event-driven
    enableFallback = true,
    autoConnect = true,
    onConnect,
    onDisconnect,
    onPriceUpdate,
    onSubscribed,
    onUnsubscribed,
    onSubscriptionError,
  } = config;

  const clientRef = useRef<WebSocketClient | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttemptsRef = useRef(10);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const priceBufferRef = useRef<Map<string, PriceUpdate>>(new Map());

  const [state, setState] = useState<UseWebSocketState>({
    connected: false,
    connecting: false,
    subscriptions: new Set(),
    refreshInterval,
    error: null,
    fallbackMode: false,
  });

  // Update refresh interval in state when config changes
  useEffect(() => {
    setState((prev) => ({
      ...prev,
      refreshInterval,
    }));
  }, [refreshInterval]);

  // Initialize WebSocket client
  useEffect(() => {
    if (!clientRef.current) {
      clientRef.current = getWebSocketClient();
    }
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  // Handle price updates (with optional batching based on refresh interval)
  const handlePriceUpdate = useCallback(
    (data: PriceUpdate) => {
      if (refreshInterval > 0) {
        // Buffer updates if refresh interval is set (batch processing)
        priceBufferRef.current.set(data.ticker, data);
      } else {
        // Immediate delivery if event-driven (refreshInterval = 0)
        onPriceUpdate?.(data);
      }
    },
    [refreshInterval, onPriceUpdate]
  );

  // Handle subscription confirmations
  const handleSubscriptionResponse = useCallback(
    (response: any) => {
      if (response.status === 'subscribed') {
        onSubscribed?.(response.ticker);
      } else if (response.status === 'unsubscribed') {
        onUnsubscribed?.(response.ticker);
      } else if (response.status === 'error') {
        onSubscriptionError?.(response.ticker, response.message);
        setState((prev) => ({
          ...prev,
          error: response.message,
        }));
      }
    },
    [onSubscribed, onUnsubscribed, onSubscriptionError]
  );

  // Connect to WebSocket server
  const connect = useCallback(async () => {
    if (!clientRef.current) return;

    try {
      setState((prev) => ({
        ...prev,
        connecting: true,
        error: null,
      }));

      await clientRef.current.connect();

      setState((prev) => ({
        ...prev,
        connected: true,
        connecting: false,
        error: null,
      }));

      reconnectAttemptsRef.current = 0;
      onConnect?.();

      // Setup event handlers
      clientRef.current.onPriceUpdate(handlePriceUpdate);
      clientRef.current.onSubscription(handleSubscriptionResponse);

      clientRef.current.onDisconnect((reason) => {
        setState((prev) => ({
          ...prev,
          connected: false,
        }));
        onDisconnect?.(reason);

        // Attempt reconnect if not intentional
        if (enableFallback && reconnectAttemptsRef.current < maxReconnectAttemptsRef.current) {
          const backoffDelay = Math.min(
            1000 * Math.pow(2, reconnectAttemptsRef.current),
            32000
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, backoffDelay);
        }
      });

      // Setup refresh interval if configured
      if (refreshInterval > 0) {
        refreshIntervalRef.current = setInterval(() => {
          priceBufferRef.current.forEach((update) => {
            onPriceUpdate?.(update);
          });
          priceBufferRef.current.clear();
        }, refreshInterval);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Connection failed';
      setState((prev) => ({
        ...prev,
        connecting: false,
        error: errorMessage,
      }));

      // Schedule reconnect attempt
      if (enableFallback && reconnectAttemptsRef.current < maxReconnectAttemptsRef.current) {
        const backoffDelay = Math.min(
          1000 * Math.pow(2, reconnectAttemptsRef.current),
          32000
        );
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          connect();
        }, backoffDelay);
      } else {
        // Enable fallback mode after max retries
        setState((prev) => ({
          ...prev,
          fallbackMode: true,
        }));
      }
    }
  }, [enableFallback, refreshInterval, handlePriceUpdate, handleSubscriptionResponse, onConnect, onDisconnect]);

  // Disconnect from WebSocket server
  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }
    setState((prev) => ({
      ...prev,
      connected: false,
      subscriptions: new Set(),
    }));
  }, []);

  // Subscribe to ticker
  const subscribe = useCallback(
    (ticker: string) => {
      if (!clientRef.current) return;

      const upperTicker = ticker.toUpperCase().trim();
      if (state.subscriptions.has(upperTicker)) {
        return; // Already subscribed
      }

      clientRef.current.subscribe(upperTicker);
      setState((prev) => ({
        ...prev,
        subscriptions: new Set([...prev.subscriptions, upperTicker]),
      }));
    },
    [state.subscriptions]
  );

  // Unsubscribe from ticker
  const unsubscribe = useCallback(
    (ticker: string) => {
      if (!clientRef.current) return;

      const upperTicker = ticker.toUpperCase().trim();
      clientRef.current.unsubscribe(upperTicker);
      setState((prev) => ({
        ...prev,
        subscriptions: new Set(
          [...prev.subscriptions].filter((t) => t !== upperTicker)
        ),
      }));
    },
    []
  );

  // Update refresh interval
  const updateRefreshInterval = useCallback((newInterval: number) => {
    setState((prev) => ({
      ...prev,
      refreshInterval: newInterval,
    }));

    // Clear existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }

    // Setup new interval if > 0
    if (newInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        priceBufferRef.current.forEach((update) => {
          onPriceUpdate?.(update);
        });
        priceBufferRef.current.clear();
      }, newInterval);
    }
  }, [onPriceUpdate]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    // State
    connected: state.connected,
    connecting: state.connecting,
    subscriptions: Array.from(state.subscriptions),
    refreshInterval: state.refreshInterval,
    error: state.error,
    fallbackMode: state.fallbackMode,

    // Methods
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    updateRefreshInterval,
  };
}
