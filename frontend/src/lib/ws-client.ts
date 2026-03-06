/**
 * WebSocket Client for TickerPulse AI
 * Manages real-time price updates via SocketIO
 */

import { io, Socket } from 'socket.io-client';

export interface PriceUpdate {
  ticker: string;
  price: number;
  currency: string;
  timestamp: string;
  change: number;
  change_pct: number;
  market?: string;
}

export interface SubscriptionResponse {
  status: 'subscribed' | 'unsubscribed' | 'error';
  message: string;
  ticker?: string;
  timestamp?: string;
}

export type PriceUpdateHandler = (data: PriceUpdate) => void;
export type SubscriptionHandler = (data: SubscriptionResponse) => void;
export type ConnectionHandler = () => void;
export type DisconnectionHandler = (reason: string) => void;

export class WebSocketClient {
  private socket: Socket | null = null;
  private url: string;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private priceHandlers: PriceUpdateHandler[] = [];
  private subscriptionHandlers: SubscriptionHandler[] = [];
  private connectionHandlers: ConnectionHandler[] = [];
  private disconnectionHandlers: DisconnectionHandler[] = [];
  private isIntentionallyClosed = false;

  constructor(url: string = '/') {
    this.url = url;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        if (this.socket?.connected) {
          resolve();
          return;
        }

        this.isIntentionallyClosed = false;
        this.socket = io(this.url, {
          namespace: '/prices',
          reconnection: true,
          reconnectionDelay: this.reconnectDelay,
          reconnectionDelayMax: this.maxReconnectDelay,
          reconnectionAttempts: this.maxReconnectAttempts,
          transports: ['websocket', 'polling'],
          autoConnect: true,
        });

        // Connection success
        this.socket.on('connect', () => {
          this.reconnectAttempts = 0;
          this.connectionHandlers.forEach((handler) => handler());
          resolve();
        });

        // Connection error
        this.socket.on('connect_error', (error) => {
          if (this.reconnectAttempts === 0) {
            reject(error);
          }
          this.reconnectAttempts++;
        });

        // Disconnection
        this.socket.on('disconnect', (reason) => {
          if (!this.isIntentionallyClosed) {
            this.disconnectionHandlers.forEach((handler) => handler(reason));
          }
        });

        // Price updates
        this.socket.on('price_update', (data: PriceUpdate) => {
          this.priceHandlers.forEach((handler) => handler(data));
        });

        // Subscription confirmations
        this.socket.on('subscription_response', (data: SubscriptionResponse) => {
          this.subscriptionHandlers.forEach((handler) => handler(data));
        });

        // Unsubscription confirmations
        this.socket.on('unsubscription_response', (data: SubscriptionResponse) => {
          this.subscriptionHandlers.forEach((handler) => handler(data));
        });

        // Error responses
        this.socket.on('error_response', (data: any) => {
          const error: SubscriptionResponse = {
            status: 'error',
            message: data?.message || 'Unknown error',
            ticker: data?.ticker,
          };
          this.subscriptionHandlers.forEach((handler) => handler(error));
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    if (this.socket?.connected) {
      this.socket.disconnect();
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  /**
   * Subscribe to price updates for a ticker
   */
  subscribe(ticker: string): void {
    if (!this.socket?.connected) {
      const error: SubscriptionResponse = {
        status: 'error',
        message: 'Not connected to WebSocket',
        ticker,
      };
      this.subscriptionHandlers.forEach((handler) => handler(error));
      return;
    }

    this.socket.emit('subscribe', {
      tickers: [ticker.toUpperCase().trim()],
    });
  }

  /**
   * Unsubscribe from price updates for a ticker
   */
  unsubscribe(ticker: string): void {
    if (!this.socket?.connected) {
      return;
    }

    this.socket.emit('unsubscribe', {
      tickers: [ticker.toUpperCase().trim()],
    });
  }

  /**
   * Get subscription status
   */
  getSubscriptionStatus(): void {
    if (!this.socket?.connected) {
      return;
    }

    this.socket.emit('get_subscription_status');
  }

  /**
   * Register handler for price updates
   */
  onPriceUpdate(handler: PriceUpdateHandler): () => void {
    this.priceHandlers.push(handler);
    // Return unsubscribe function
    return () => {
      const index = this.priceHandlers.indexOf(handler);
      if (index > -1) {
        this.priceHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Register handler for subscription confirmations
   */
  onSubscription(handler: SubscriptionHandler): () => void {
    this.subscriptionHandlers.push(handler);
    // Return unsubscribe function
    return () => {
      const index = this.subscriptionHandlers.indexOf(handler);
      if (index > -1) {
        this.subscriptionHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Register handler for connection
   */
  onConnect(handler: ConnectionHandler): () => void {
    this.connectionHandlers.push(handler);
    // Return unsubscribe function
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Register handler for disconnection
   */
  onDisconnect(handler: DisconnectionHandler): () => void {
    this.disconnectionHandlers.push(handler);
    // Return unsubscribe function
    return () => {
      const index = this.disconnectionHandlers.indexOf(handler);
      if (index > -1) {
        this.disconnectionHandlers.splice(index, 1);
      }
    };
  }
}

// Global client instance
let globalClient: WebSocketClient | null = null;

/**
 * Get or create global WebSocket client
 */
export function getWebSocketClient(url?: string): WebSocketClient {
  if (!globalClient) {
    globalClient = new WebSocketClient(url);
  }
  return globalClient;
}
