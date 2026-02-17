"""
TickerPulse AI v3.0 - Stock Data Fetcher Tool (CrewAI Compatible)
Wraps the pluggable data_providers system to fetch stock quotes and historical data.
Falls back through the provider chain automatically.
"""

import json
import logging
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Try to import CrewAI BaseTool; fall back to a minimal shim
# ------------------------------------------------------------------
try:
    from crewai.tools import BaseTool as _CrewAIBaseTool
    from pydantic import BaseModel, Field

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    # Minimal shim so the class definition doesn't break
    class BaseModel:  # type: ignore[no-redef]
        pass

    class Field:  # type: ignore[no-redef]
        def __init__(self, *a, **kw):
            pass

    class _CrewAIBaseTool:  # type: ignore[no-redef]
        name: str = ""
        description: str = ""

        def _run(self, *args, **kwargs):
            raise NotImplementedError


# ------------------------------------------------------------------
# Pydantic input schema (only used when CrewAI is available)
# ------------------------------------------------------------------
if CREWAI_AVAILABLE:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField

    class StockDataInput(_PydanticBaseModel):
        """Input schema for the Stock Data Fetcher tool."""
        ticker: str = _PydanticField(..., description="Stock ticker symbol (e.g. AAPL, MSFT, RELIANCE.NS)")
        action: str = _PydanticField(
            default="quote",
            description="Action to perform: 'quote' for current price, 'history' for historical data"
        )
        period: str = _PydanticField(
            default="1mo",
            description="Historical data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"
        )
else:
    StockDataInput = None  # type: ignore[assignment,misc]


# ------------------------------------------------------------------
# Helper: create a DataProviderRegistry lazily
# ------------------------------------------------------------------
_registry_cache = None


def _get_registry():
    """Return a cached DataProviderRegistry instance."""
    global _registry_cache
    if _registry_cache is None:
        try:
            from backend.data_providers import create_registry
            _registry_cache = create_registry()
        except ImportError:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                from backend.data_providers import create_registry
                _registry_cache = create_registry()
            except Exception as e:
                logger.error(f"Failed to create data provider registry: {e}")
                _registry_cache = None
    return _registry_cache


# ------------------------------------------------------------------
# The Tool
# ------------------------------------------------------------------
class StockDataFetcher(_CrewAIBaseTool):
    """CrewAI-compatible tool that fetches stock quotes and historical data
    through the pluggable data provider chain (Polygon -> Finnhub ->
    Alpha Vantage -> Yahoo Finance)."""

    name: str = "Stock Data Fetcher"
    description: str = (
        "Fetches real-time stock quotes and historical OHLCV price data. "
        "Provide a ticker symbol and optionally an action ('quote' or 'history') "
        "and a period (1d, 5d, 1mo, 3mo, 6mo, 1y). "
        "Falls back through multiple data providers automatically."
    )

    if CREWAI_AVAILABLE and StockDataInput is not None:
        args_schema: Type[BaseModel] = StockDataInput  # type: ignore[assignment]

    def _run(self, ticker: str, action: str = "quote", period: str = "1mo", **kwargs) -> str:
        """Execute the tool -- called by CrewAI or directly."""
        ticker = ticker.strip().upper()

        if action == "quote":
            return self._get_quote(ticker)
        elif action == "history":
            return self._get_history(ticker, period)
        else:
            return json.dumps({"error": f"Unknown action '{action}'. Use 'quote' or 'history'."})

    # ---- public helpers (usable outside CrewAI) -----------------------

    def get_current_quote(self, ticker: str) -> Dict[str, Any]:
        """Return a dict with current quote data, or an error dict."""
        return json.loads(self._get_quote(ticker.strip().upper()))

    def get_historical_prices(self, ticker: str, period: str = "1mo") -> Dict[str, Any]:
        """Return a dict with historical price data, or an error dict."""
        return json.loads(self._get_history(ticker.strip().upper(), period))

    # ---- internals ----------------------------------------------------

    def _get_quote(self, ticker: str) -> str:
        registry = _get_registry()
        if registry is None:
            return json.dumps({"error": "No data providers available"})

        try:
            quote = registry.get_quote(ticker)
            if quote is None:
                return json.dumps({"error": f"No quote data available for {ticker}"})

            return json.dumps({
                "ticker": quote.ticker,
                "price": quote.price,
                "open": quote.open,
                "high": quote.high,
                "low": quote.low,
                "volume": quote.volume,
                "change": quote.change,
                "change_percent": quote.change_percent,
                "currency": quote.currency,
                "timestamp": quote.timestamp.isoformat() if quote.timestamp else None,
                "source": quote.source,
            })
        except Exception as e:
            logger.error(f"Error fetching quote for {ticker}: {e}")
            return json.dumps({"error": str(e)})

    def _get_history(self, ticker: str, period: str) -> str:
        registry = _get_registry()
        if registry is None:
            return json.dumps({"error": "No data providers available"})

        try:
            history = registry.get_historical(ticker, period)
            if history is None or not history.bars:
                return json.dumps({"error": f"No historical data available for {ticker} ({period})"})

            bars_data = []
            for bar in history.bars:
                bars_data.append({
                    "timestamp": bar.timestamp,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                })

            closes = [b.close for b in history.bars]
            latest_close = closes[-1] if closes else 0
            earliest_close = closes[0] if closes else 0
            period_change = latest_close - earliest_close
            period_change_pct = (period_change / earliest_close * 100) if earliest_close else 0
            high_of_period = max(b.high for b in history.bars)
            low_of_period = min(b.low for b in history.bars)
            avg_volume = sum(b.volume for b in history.bars) / len(history.bars) if history.bars else 0

            return json.dumps({
                "ticker": history.ticker,
                "period": history.period,
                "source": history.source,
                "num_bars": len(bars_data),
                "latest_close": latest_close,
                "period_change": round(period_change, 4),
                "period_change_pct": round(period_change_pct, 4),
                "high_of_period": high_of_period,
                "low_of_period": low_of_period,
                "avg_volume": round(avg_volume),
                "bars": bars_data,
            })
        except Exception as e:
            logger.error(f"Error fetching history for {ticker}: {e}")
            return json.dumps({"error": str(e)})
