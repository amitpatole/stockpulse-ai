"""
TickerPulse AI v3.0 - Options Data Provider (Mock Implementation)
Placeholder provider for options data. In production, would integrate with
market data APIs like Market Data, Finnhub, or custom data sources.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OptionFlow:
    """Represents an options flow data point."""

    ticker: str
    flow_type: str  # 'call_spike' | 'put_spike' | 'unusual_volume'
    option_type: str  # 'call' or 'put'
    strike_price: float
    expiry_date: str  # YYYY-MM-DD
    volume: int
    open_interest: int
    unusual_ratio: float  # current_volume / 20-day_avg


class OptionsDataProvider:
    """Mock options data provider (placeholder for production integration)."""

    def __init__(self):
        """Initialize the provider."""
        self._cache = {}

    def get_flows(self, ticker: str) -> Optional[List[OptionFlow]]:
        """Fetch options flows for a ticker.

        In production, this would call a market data API.
        For now, returns None (no data available).

        Parameters
        ----------
        ticker : str
            Stock ticker symbol

        Returns
        -------
        Optional[List[OptionFlow]]
            List of option flows, or None if unavailable
        """
        logger.warning(
            f"OptionsDataProvider.get_flows() is not implemented for {ticker}. "
            "To enable options tracking, implement integration with Market Data API "
            "(e.g., Finnhub, Market Data, or custom data source)."
        )
        return None

    def get_put_call_ratio(self, ticker: str) -> Optional[float]:
        """Get put/call volume ratio for a ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol

        Returns
        -------
        Optional[float]
            Put volume / Call volume ratio, or None
        """
        return None

    def get_20day_avg_volume(
        self, ticker: str, option_type: str, strike: float
    ) -> Optional[int]:
        """Get 20-day average volume for a specific option contract.

        Parameters
        ----------
        ticker : str
            Stock ticker
        option_type : str
            'call' or 'put'
        strike : float
            Strike price

        Returns
        -------
        Optional[int]
            Average daily volume over last 20 days, or None
        """
        return None