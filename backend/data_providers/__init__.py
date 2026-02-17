"""
TickerPulse AI v3.0 -- Pluggable Data Provider System

This package provides a provider-agnostic data layer that lets users
plug in whatever stock data subscriptions they already pay for.

Registered providers (in fallback order):
  1. Polygon.io     -- requires POLYGON_API_KEY
  2. Finnhub        -- requires FINNHUB_API_KEY
  3. Alpha Vantage  -- requires ALPHA_VANTAGE_KEY
  4. Yahoo Finance  -- always available (free, no key needed)

Usage::

    from backend.data_providers import create_registry

    registry = create_registry()

    # Get a quote with automatic provider fallback
    quote = registry.get_quote('AAPL')

    # List all registered providers and their status
    for p in registry.list_providers():
        print(p['display_name'], '-- available' if p['is_available'] else '-- not configured')

To add your own provider, copy ``custom_provider.py`` to a new file,
implement the four required methods, and register it in ``create_registry()``
below.
"""

import logging
from typing import Optional

from .base import (
    DataProvider,
    DataProviderRegistry,
    PriceBar,
    PriceHistory,
    ProviderInfo,
    Quote,
    TickerResult,
)
from .yfinance_provider import YFinanceProvider
from .polygon_provider import PolygonProvider
from .finnhub_provider import FinnhubProvider
from .alpha_vantage_provider import AlphaVantageProvider
from .custom_provider import CustomProvider

logger = logging.getLogger(__name__)

__all__ = [
    # Data classes
    'Quote',
    'PriceBar',
    'PriceHistory',
    'TickerResult',
    'ProviderInfo',
    # Base / registry
    'DataProvider',
    'DataProviderRegistry',
    # Concrete providers
    'YFinanceProvider',
    'PolygonProvider',
    'FinnhubProvider',
    'AlphaVantageProvider',
    'CustomProvider',
    # Factory
    'create_registry',
]


def create_registry(
    polygon_key: Optional[str] = None,
    finnhub_key: Optional[str] = None,
    alpha_vantage_key: Optional[str] = None,
    primary: Optional[str] = None,
) -> DataProviderRegistry:
    """Create and return a fully-configured :class:`DataProviderRegistry`.

    The function auto-discovers which providers have API keys configured
    by checking:
      1. Explicit keyword arguments passed to this function.
      2. The ``Config`` object in ``backend.config`` (environment variables).

    Providers with valid API keys are registered in this order (first =
    highest priority):
      - polygon
      - finnhub
      - alpha_vantage
      - yfinance  (always last -- free fallback, no key needed)

    Parameters
    ----------
    polygon_key : str, optional
        Override the Polygon.io API key (instead of reading from Config).
    finnhub_key : str, optional
        Override the Finnhub API key.
    alpha_vantage_key : str, optional
        Override the Alpha Vantage API key.
    primary : str, optional
        Name of the provider to use as the primary source.  If not given,
        the first provider with a configured API key is used.

    Returns
    -------
    DataProviderRegistry
    """

    # ------------------------------------------------------------------
    # Resolve API keys from Config if not passed explicitly
    # ------------------------------------------------------------------
    try:
        from backend.config import Config
    except ImportError:
        # Allow running outside the full app context
        try:
            from config import Config  # type: ignore[no-redef]
        except ImportError:
            Config = None  # type: ignore[assignment,misc]

    def _cfg(attr: str) -> str:
        """Safely read an attribute from Config, returning '' on failure."""
        if Config is None:
            return ''
        return getattr(Config, attr, '') or ''

    polygon_key = polygon_key or _cfg('POLYGON_API_KEY')
    finnhub_key = finnhub_key or _cfg('FINNHUB_API_KEY')
    alpha_vantage_key = alpha_vantage_key or _cfg('ALPHA_VANTAGE_KEY')

    # ------------------------------------------------------------------
    # Build the registry
    # ------------------------------------------------------------------
    registry = DataProviderRegistry()

    # Premium / freemium providers first (in preferred priority order)
    if polygon_key:
        try:
            registry.register('polygon', PolygonProvider(api_key=polygon_key))
            logger.info("Registered data provider: Polygon.io")
        except Exception as e:
            logger.warning(f"Failed to register Polygon provider: {e}")

    if finnhub_key:
        try:
            registry.register('finnhub', FinnhubProvider(api_key=finnhub_key))
            logger.info("Registered data provider: Finnhub")
        except Exception as e:
            logger.warning(f"Failed to register Finnhub provider: {e}")

    if alpha_vantage_key:
        try:
            registry.register('alpha_vantage', AlphaVantageProvider(api_key=alpha_vantage_key))
            logger.info("Registered data provider: Alpha Vantage")
        except Exception as e:
            logger.warning(f"Failed to register Alpha Vantage provider: {e}")

    # -----------------------------------------------------------------------
    # To register your own custom provider, uncomment and edit the lines
    # below (or add similar lines for any DataProvider subclass):
    #
    #   from .my_broker_provider import MyBrokerProvider
    #   my_key = _cfg('MY_BROKER_API_KEY')  # reads MY_BROKER_API_KEY env var
    #   if my_key:
    #       registry.register('my_broker', MyBrokerProvider(api_key=my_key))
    # -----------------------------------------------------------------------

    # Yahoo Finance is always registered as the last-resort free fallback
    try:
        registry.register('yfinance', YFinanceProvider())
        logger.info("Registered data provider: Yahoo Finance (free fallback)")
    except Exception as e:
        logger.warning(f"Failed to register YFinance provider: {e}")

    # ------------------------------------------------------------------
    # Set the primary provider
    # ------------------------------------------------------------------
    if primary and primary in ('polygon', 'finnhub', 'alpha_vantage', 'yfinance'):
        registry.set_primary(primary)
    else:
        # Auto-select: first provider with a key, or yfinance
        for name in ('polygon', 'finnhub', 'alpha_vantage', 'yfinance'):
            provider = registry.get_provider(name)
            if provider and provider.is_available():
                registry.set_primary(name)
                break

    primary_provider = registry.get_primary()
    if primary_provider:
        info = primary_provider.get_provider_info()
        logger.info(f"Primary data provider: {info.display_name}")
    else:
        logger.warning("No data providers available!")

    return registry
