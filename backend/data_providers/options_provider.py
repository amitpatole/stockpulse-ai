```python
"""
TickerPulse AI - Options Data Provider Abstract Base Class
Defines the interface for options data collection from various sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from datetime import date


@dataclass
class OptionContract:
    """Represents a single options contract."""
    ticker: str
    contract: str  # e.g., "AAPL 150C 2026-03-31"
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: date
    volume: int
    open_interest: int
    bid_ask_spread: float  # in dollars
    iv_percentile: int  # 0-100
    bid: float
    ask: float
    last_price: float
    implied_volatility: float


class OptionsDataProvider(ABC):
    """Abstract base class for options data providers."""

    @abstractmethod
    def get_contracts(self, ticker: str) -> Optional[List[OptionContract]]:
        """Fetch all options contracts for a given ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol (e.g., 'AAPL').

        Returns
        -------
        Optional[List[OptionContract]]
            List of option contracts, or None if fetch fails.
        """
        pass

    @abstractmethod
    def get_put_call_ratio(self, ticker: str) -> Optional[float]:
        """Get the put/call ratio for a ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.

        Returns
        -------
        Optional[float]
            Put volume / Call volume ratio, or None if unavailable.
        """
        pass

    @abstractmethod
    def get_open_interest_trend(self, ticker: str) -> Optional[dict]:
        """Get open interest trend data for a ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.

        Returns
        -------
        Optional[dict]
            Dictionary with keys: 'calls_oi', 'puts_oi', 'calls_oi_delta', 'puts_oi_delta'.
            None if unavailable.
        """
        pass
```