"""
Chart rendering input validation utilities.

Centralised rules shared across yfinance_provider.py and ai_analytics.py so
that both providers apply identical checks without duplicating the math.
"""

import math
import logging
from typing import List

logger = logging.getLogger(__name__)

# Timestamp bounds: 2000-01-01T00:00:00Z to 2100-01-01T00:00:00Z (Unix seconds)
_TS_MIN = 946684800
_TS_MAX = 4102444800


def is_valid_price(v) -> bool:
    """Return True if *v* is a finite positive number."""
    try:
        return math.isfinite(float(v)) and float(v) > 0
    except (TypeError, ValueError):
        return False


def is_valid_timestamp(ts: int) -> bool:
    """Return True if *ts* is a Unix-second timestamp in the range 2000–2100."""
    try:
        ts = int(ts)
        return _TS_MIN < ts < _TS_MAX
    except (TypeError, ValueError):
        return False


def validate_ohlc_relationships(o, h, l, c) -> bool:
    """Return True when low <= open <= high and low <= close <= high."""
    try:
        o, h, l, c = float(o), float(h), float(l), float(c)
        return l <= o <= h and l <= c <= h
    except (TypeError, ValueError):
        return False


def validate_ohlcv_arrays(
    open_: List,
    high: List,
    low: List,
    close: List,
    volume: List,
    timestamps: List,
) -> None:
    """Raise ValueError if any array length differs from the others."""
    lengths = {
        'open': len(open_),
        'high': len(high),
        'low': len(low),
        'close': len(close),
        'volume': len(volume),
        'timestamps': len(timestamps),
    }
    unique = set(lengths.values())
    if len(unique) > 1:
        raise ValueError(f"OHLCV array length mismatch: {lengths}")


def sanitize_price_bar(bar: dict, ticker: str) -> dict:
    """Validate and return a single OHLCV bar dict.

    Raises ValueError with the offending field and ticker in the message if
    any field is invalid.  Logs a WARNING before raising.
    """
    for field in ('open', 'high', 'low', 'close'):
        v = bar.get(field)
        if not is_valid_price(v):
            logger.warning(
                "Invalid chart data: field=%s ticker=%s value=%r", field, ticker, v
            )
            raise ValueError(f"{field} out of range for {ticker}")

    if not validate_ohlc_relationships(
        bar['open'], bar['high'], bar['low'], bar['close']
    ):
        logger.warning(
            "OHLC relationship violated for %s: O=%r H=%r L=%r C=%r",
            ticker, bar['open'], bar['high'], bar['low'], bar['close'],
        )
        raise ValueError(f"ohlc_relationship out of range for {ticker}")

    ts = bar.get('timestamp')
    if not is_valid_timestamp(ts):
        logger.warning("Invalid timestamp for %s: %r", ticker, ts)
        raise ValueError(f"timestamp out of range for {ticker}")

    return bar
