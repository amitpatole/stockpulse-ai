from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Quote:
    """Real-time or delayed stock quote"""
    ticker: str
    price: float
    open: float
    high: float
    low: float
    volume: int
    timestamp: datetime
    currency: str = 'USD'
    change: float = 0.0
    change_percent: float = 0.0
    source: str = ''


@dataclass
class PriceBar:
    """Single OHLCV bar"""
    timestamp: int  # Unix timestamp
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class PriceHistory:
    """Historical price data"""
    ticker: str
    bars: List[PriceBar]
    period: str
    source: str = ''


@dataclass
class TickerResult:
    """Search result for ticker lookup"""
    ticker: str
    name: str
    exchange: str = ''
    type: str = 'stock'  # stock, etf, crypto, index
    market: str = 'US'


@dataclass
class ProviderInfo:
    """Metadata about a data provider"""
    name: str
    display_name: str
    tier: str  # 'free', 'freemium', 'premium'
    requires_key: bool
    supported_markets: List[str]
    has_realtime: bool
    rate_limit_per_minute: int
    description: str


class DataProvider(ABC):
    """Abstract base class for all stock data providers"""

    def __init__(self, api_key: str = ''):
        self.api_key = api_key
        self._request_count = 0
        self._last_request_time = None

    @abstractmethod
    def get_quote(self, ticker: str) -> Optional[Quote]:
        """Get current quote for a ticker"""
        pass

    @abstractmethod
    def get_historical(self, ticker: str, period: str = '1mo') -> Optional[PriceHistory]:
        """Get historical price data. Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"""
        pass

    @abstractmethod
    def search_ticker(self, query: str) -> List[TickerResult]:
        """Search for tickers by name or symbol"""
        pass

    @abstractmethod
    def get_provider_info(self) -> ProviderInfo:
        """Return provider metadata"""
        pass

    def is_available(self) -> bool:
        """Check if provider is configured and accessible"""
        info = self.get_provider_info()
        if info.requires_key and not self.api_key:
            return False
        return True

    def test_connection(self) -> Dict[str, Any]:
        """Test if the provider connection works"""
        try:
            result = self.get_quote('AAPL')
            if result:
                return {'success': True, 'provider': self.get_provider_info().name, 'sample_price': result.price}
            return {'success': False, 'error': 'No data returned for AAPL'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class DataProviderRegistry:
    """Registry and fallback chain for data providers"""

    def __init__(self):
        self._providers: Dict[str, DataProvider] = {}
        self._fallback_order: List[str] = []
        self._primary: Optional[str] = None
        self.on_fallback: Optional[Callable[[str, str, str], None]] = None

    def register(self, name: str, provider: DataProvider):
        self._providers[name] = provider
        if name not in self._fallback_order:
            self._fallback_order.append(name)

    def set_primary(self, name: str):
        if name in self._providers:
            self._primary = name

    def set_fallback_order(self, order: List[str]):
        self._fallback_order = [n for n in order if n in self._providers]

    def get_provider(self, name: str) -> Optional[DataProvider]:
        return self._providers.get(name)

    def get_primary(self) -> Optional[DataProvider]:
        if self._primary:
            return self._providers.get(self._primary)
        # Return first available
        for name in self._fallback_order:
            provider = self._providers[name]
            if provider.is_available():
                return provider
        return None

    def get_quote(self, ticker: str) -> Optional[Quote]:
        """Get quote with automatic fallback"""
        providers_to_try = []
        if self._primary and self._primary in self._providers:
            providers_to_try.append(self._primary)
        providers_to_try.extend([n for n in self._fallback_order if n != self._primary])

        first_failed: Optional[str] = None
        first_fail_reason: str = 'exception'
        for name in providers_to_try:
            provider = self._providers[name]
            if not provider.is_available():
                continue
            try:
                result = provider.get_quote(ticker)
                if result:
                    if first_failed is not None and self.on_fallback is not None:
                        self.on_fallback(first_failed, name, first_fail_reason)
                    return result
                if first_failed is None:
                    first_failed = name
                    first_fail_reason = 'no_data'
            except Exception as e:
                logger.warning(f"Provider {name} failed for {ticker}: {e}")
                if first_failed is None:
                    first_failed = name
                    first_fail_reason = 'exception'
                continue
        return None

    def get_historical(self, ticker: str, period: str = '1mo') -> Optional[PriceHistory]:
        """Get historical data with automatic fallback"""
        providers_to_try = []
        if self._primary and self._primary in self._providers:
            providers_to_try.append(self._primary)
        providers_to_try.extend([n for n in self._fallback_order if n != self._primary])

        first_failed: Optional[str] = None
        first_fail_reason: str = 'exception'
        for name in providers_to_try:
            provider = self._providers[name]
            if not provider.is_available():
                continue
            try:
                result = provider.get_historical(ticker, period)
                if result and result.bars:
                    if first_failed is not None and self.on_fallback is not None:
                        self.on_fallback(first_failed, name, first_fail_reason)
                    return result
                if first_failed is None:
                    first_failed = name
                    first_fail_reason = 'no_data'
            except Exception as e:
                logger.warning(f"Provider {name} failed historical for {ticker}: {e}")
                if first_failed is None:
                    first_failed = name
                    first_fail_reason = 'exception'
                continue
        return None

    def search_ticker(self, query: str) -> List[TickerResult]:
        """Search tickers using primary provider"""
        provider = self.get_primary()
        if provider:
            try:
                return provider.search_ticker(query)
            except Exception as e:
                logger.warning(f"Ticker search failed: {e}")
        return []

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all registered providers with status"""
        result = []
        for name, provider in self._providers.items():
            info = provider.get_provider_info()
            result.append({
                'name': info.name,
                'display_name': info.display_name,
                'tier': info.tier,
                'is_available': provider.is_available(),
                'is_primary': name == self._primary,
                'has_realtime': info.has_realtime,
                'supported_markets': info.supported_markets,
                'rate_limit_per_minute': info.rate_limit_per_minute,
                'description': info.description,
            })
        return result
