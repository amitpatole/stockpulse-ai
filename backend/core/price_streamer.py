"""
TickerPulse AI v3.0 - Price Streamer Service
Manages real-time price updates and broadcasts to subscribed clients via WebSocket.
Runs as a background service to monitor stock prices and emit updates.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable

from backend.core.stock_manager import get_all_stocks

logger = logging.getLogger(__name__)


class PriceStreamer:
    """Manages real-time price streaming and broadcasting to subscribed clients."""

    def __init__(self, broadcast_fn: Optional[Callable] = None, update_interval: int = 5):
        """Initialize price streamer.

        Args:
            broadcast_fn: Callback function to broadcast price updates
            update_interval: Seconds between price checks (default: 5)
        """
        self.broadcast_fn = broadcast_fn
        self.update_interval = update_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_prices: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the price streamer thread."""
        if self._running:
            logger.warning("Price streamer already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
        logger.info("Price streamer started")

    def stop(self) -> None:
        """Stop the price streamer thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Price streamer stopped")

    def _stream_loop(self) -> None:
        """Main streaming loop that checks prices and broadcasts updates."""
        while self._running:
            try:
                self._check_and_broadcast_prices()
            except Exception as exc:
                logger.error(f"Error in price stream loop: {exc}")

            time.sleep(self.update_interval)

    def _check_and_broadcast_prices(self) -> None:
        """Check current prices and broadcast changes to subscribers."""
        try:
            all_stocks = get_all_stocks()

            for stock in all_stocks:
                ticker = stock.get('ticker', '').upper()
                if not ticker:
                    continue

                # Build current price data
                price_data = {
                    'ticker': ticker,
                    'price': stock.get('current_price', 0),
                    'currency': stock.get('currency', 'USD'),
                    'timestamp': stock.get('updated_at', datetime.now(timezone.utc).isoformat()),
                    'change': stock.get('day_change', 0),
                    'change_pct': stock.get('day_change_percent', 0),
                    'market': stock.get('market', 'US'),
                }

                # Check if price changed significantly
                if self._should_broadcast(ticker, price_data):
                    self._broadcast_price(ticker, price_data)

                    # Update last known price
                    with self._lock:
                        self._last_prices[ticker] = price_data

        except Exception as exc:
            logger.error(f"Error checking prices: {exc}")

    def _should_broadcast(self, ticker: str, new_price: Dict[str, Any]) -> bool:
        """Determine if price change should be broadcast.

        Broadcasts if:
        - First time seeing this ticker
        - Price changed by at least 0.01%
        - Change percentage changed significantly
        """
        with self._lock:
            if ticker not in self._last_prices:
                return True

            last = self._last_prices[ticker]

            # Detect price change
            price_change = abs(new_price.get('price', 0) - last.get('price', 0))
            if price_change > 0.01:
                return True

            # Detect percentage change
            pct_change_diff = abs(
                new_price.get('change_pct', 0) - last.get('change_pct', 0)
            )
            if pct_change_diff > 0.01:
                return True

        return False

    def _broadcast_price(self, ticker: str, price_data: Dict[str, Any]) -> None:
        """Broadcast price update to subscribers."""
        if self.broadcast_fn:
            try:
                self.broadcast_fn(ticker, price_data)
            except Exception as exc:
                logger.error(f"Error broadcasting price for {ticker}: {exc}")


# Global instance (initialized in app.py)
price_streamer: Optional[PriceStreamer] = None


def init_price_streamer(broadcast_fn: Callable) -> PriceStreamer:
    """Initialize and start the global price streamer.

    Args:
        broadcast_fn: Function to call to broadcast price updates

    Returns:
        PriceStreamer instance
    """
    global price_streamer
    price_streamer = PriceStreamer(broadcast_fn=broadcast_fn)
    price_streamer.start()
    return price_streamer


def get_price_streamer() -> Optional[PriceStreamer]:
    """Get the global price streamer instance."""
    return price_streamer
