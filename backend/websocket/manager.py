"""
WebSocket Manager - Thread-safe connection and subscription management.
Handles client registration, ticker subscriptions, and price broadcast logic.
"""

import threading
import logging
from typing import Dict, Callable, Set, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Ticker validation: alphanumeric + dot/dash (e.g., AAPL, BRK.A, BRK-B, RELIANCE.NS)
TICKER_PATTERN_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-'
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 5


class WebSocketManager:
    """Thread-safe WebSocket connection and subscription manager."""

    def __init__(self, max_connections: int = 1000) -> None:
        """Initialize the WebSocket manager.

        Parameters
        ----------
        max_connections : int
            Maximum number of concurrent WebSocket connections. Default: 1000.
        """
        self._lock = threading.RLock()
        self._clients: Dict[str, Callable] = {}  # client_id -> send_func
        self._subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of tickers
        self._ticker_clients: Dict[str, Set[str]] = {}  # ticker -> set of client_ids
        self._max_connections = max_connections

    def register_client(self, client_id: str, send_func: Callable[[Dict[str, Any]], None]) -> bool:
        """Register a WebSocket client.

        Parameters
        ----------
        client_id : str
            Unique identifier for the client.
        send_func : Callable
            Function to call to send messages to the client.
            Signature: send_func(message_dict) -> None

        Returns
        -------
        bool
            True if registered successfully, False if max connections exceeded.
        """
        with self._lock:
            if len(self._clients) >= self._max_connections:
                logger.warning(
                    f"WebSocket connection limit ({self._max_connections}) reached. "
                    f"Rejecting client {client_id}"
                )
                return False

            self._clients[client_id] = send_func
            self._subscriptions[client_id] = set()
            logger.info(f"WebSocket client registered: {client_id}")
            return True

    def unregister_client(self, client_id: str) -> None:
        """Unregister a WebSocket client and clean up subscriptions.

        Parameters
        ----------
        client_id : str
            Unique identifier for the client to unregister.
        """
        with self._lock:
            if client_id in self._clients:
                # Remove from all ticker subscriptions
                for ticker in list(self._subscriptions.get(client_id, [])):
                    if ticker in self._ticker_clients:
                        self._ticker_clients[ticker].discard(client_id)
                        if not self._ticker_clients[ticker]:
                            del self._ticker_clients[ticker]

                del self._clients[client_id]
                if client_id in self._subscriptions:
                    del self._subscriptions[client_id]

                logger.info(f"WebSocket client unregistered: {client_id}")

    def subscribe(self, client_id: str, tickers: list[str]) -> Dict[str, Any]:
        """Subscribe a client to one or more stock tickers.

        Parameters
        ----------
        client_id : str
            Client identifier.
        tickers : list[str]
            List of stock ticker symbols to subscribe to.

        Returns
        -------
        dict
            Response with keys:
            - 'subscribed': list of successfully subscribed tickers
            - 'errors': list of error dicts with 'ticker' and 'code'
            - 'total': total number of subscriptions for this client
            - 'error': (if client not registered) error message
        """
        with self._lock:
            if client_id not in self._clients:
                return {'error': 'Client not registered'}

            subscribed: list[str] = []
            errors: list[Dict[str, Any]] = []

            for ticker in tickers:
                validation_error = self._validate_ticker(ticker)
                if validation_error:
                    errors.append({
                        'ticker': ticker,
                        'code': validation_error
                    })
                    continue

                ticker_upper = ticker.upper()

                # Add to client subscriptions
                if ticker_upper not in self._subscriptions[client_id]:
                    self._subscriptions[client_id].add(ticker_upper)

                    # Add to ticker -> clients mapping
                    if ticker_upper not in self._ticker_clients:
                        self._ticker_clients[ticker_upper] = set()
                    self._ticker_clients[ticker_upper].add(client_id)

                    subscribed.append(ticker_upper)

            total = len(self._subscriptions[client_id])
            return {
                'subscribed': subscribed,
                'errors': errors,
                'total': total
            }

    def unsubscribe(self, client_id: str, tickers: list[str]) -> Dict[str, Any]:
        """Unsubscribe a client from stock tickers.

        Parameters
        ----------
        client_id : str
            Client identifier.
        tickers : list[str]
            List of tickers to unsubscribe from.

        Returns
        -------
        dict
            Response with keys:
            - 'unsubscribed': list of unsubscribed tickers
            - 'total': remaining subscription count
            - 'error': (if client not registered) error message
        """
        with self._lock:
            if client_id not in self._clients:
                return {'error': 'Client not registered'}

            unsubscribed: list[str] = []

            for ticker in tickers:
                ticker_upper = ticker.upper()
                if ticker_upper in self._subscriptions[client_id]:
                    self._subscriptions[client_id].remove(ticker_upper)
                    unsubscribed.append(ticker_upper)

                    # Remove from ticker -> clients mapping
                    if ticker_upper in self._ticker_clients:
                        self._ticker_clients[ticker_upper].discard(client_id)
                        if not self._ticker_clients[ticker_upper]:
                            del self._ticker_clients[ticker_upper]

            total = len(self._subscriptions[client_id])
            return {
                'unsubscribed': unsubscribed,
                'total': total
            }

    def broadcast_price_update(self, ticker: str, data: Dict[str, Any]) -> int:
        """Broadcast a price update to all clients subscribed to a ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        data : dict
            Price data with keys like 'current_price', 'price_change', 'rsi', etc.

        Returns
        -------
        int
            Number of clients that received the update.
        """
        with self._lock:
            ticker_upper = ticker.upper()
            client_ids = self._ticker_clients.get(ticker_upper, set()).copy()

        if not client_ids:
            return 0

        # Build message
        message = {
            'type': 'price_update',
            'data': {
                'ticker': ticker_upper,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                **data
            }
        }

        # Send to each client
        sent_count = 0
        for client_id in client_ids:
            with self._lock:
                if client_id in self._clients:
                    try:
                        self._clients[client_id](message)
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Error sending to client {client_id}: {e}")

        return sent_count

    def get_connection_count(self) -> int:
        """Get the number of connected clients.

        Returns
        -------
        int
            Number of registered clients.
        """
        with self._lock:
            return len(self._clients)

    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """Get all tickers a client is subscribed to.

        Parameters
        ----------
        client_id : str
            Client identifier.

        Returns
        -------
        set
            Set of subscribed ticker symbols (uppercase).
        """
        with self._lock:
            return self._subscriptions.get(client_id, set()).copy()

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _validate_ticker(self, ticker: str) -> str | None:
        """Validate a ticker symbol.

        Parameters
        ----------
        ticker : str
            Ticker to validate.

        Returns
        -------
        str | None
            Error code if invalid (e.g., 'invalid_format', 'invalid_length'),
            or None if valid.
        """
        if not ticker:
            return 'invalid_length'

        # Allow dot and dash in addition to alphanumeric (e.g., BRK.A, BRK-B)
        if not all(c in TICKER_PATTERN_CHARS for c in ticker):
            return 'invalid_format'

        if not (TICKER_MIN_LENGTH <= len(ticker) <= TICKER_MAX_LENGTH):
            return 'invalid_length'

        return None
