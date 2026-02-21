"""Chart data validation utilities for TickerPulse AI.

Provides sanitize_price_bar and validate_ohlcv_arrays to reject corrupt or
injected values before they reach chart renderers or analytics pipelines.
"""

import math
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Sanity bounds for timestamps (Unix seconds)
_MIN_TIMESTAMP = 315532800   # 1980-01-01
_MAX_TIMESTAMP = 4102444800  # 2100-01-01


def _is_finite_positive(value: Any) -> bool:
    """Return True if value is a finite, strictly-positive number."""
    try:
        f = float(value)
        return math.isfinite(f) and f > 0
    except (TypeError, ValueError):
        return False


def _is_finite_non_negative(value: Any) -> bool:
    """Return True if value is a finite, non-negative number (zero allowed)."""
    try:
        f = float(value)
        return math.isfinite(f) and f >= 0
    except (TypeError, ValueError):
        return False


def sanitize_price_bar(bar: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate a single OHLCV price-bar dict.

    Checks:
    - open, high, low, close are finite and > 0
    - high >= low (OHLC relationship)
    - timestamp is an integer within sensible Unix-second bounds
    - volume is finite and >= 0 (zero is valid on illiquid days)

    Returns the bar unchanged if valid, or None if the bar should be dropped.
    """
    if not isinstance(bar, dict):
        return None

    # Validate OHLC price fields — must be finite and strictly positive
    for field in ('open', 'high', 'low', 'close'):
        if not _is_finite_positive(bar.get(field)):
            logger.debug(
                "sanitize_price_bar: dropping bar with invalid %s=%r", field, bar.get(field)
            )
            return None

    h = float(bar['high'])
    l = float(bar['low'])

    if h < l:
        logger.debug(
            "sanitize_price_bar: dropping bar where high(%s) < low(%s)", h, l
        )
        return None

    # Validate timestamp
    ts = bar.get('timestamp')
    try:
        ts_int = int(ts)
    except (TypeError, ValueError):
        logger.debug(
            "sanitize_price_bar: dropping bar with non-integer timestamp=%r", ts
        )
        return None
    if not (_MIN_TIMESTAMP <= ts_int <= _MAX_TIMESTAMP):
        logger.debug(
            "sanitize_price_bar: dropping bar with out-of-range timestamp=%s", ts_int
        )
        return None

    # Validate volume — must be finite and non-negative
    vol = bar.get('volume')
    if not _is_finite_non_negative(vol):
        logger.debug(
            "sanitize_price_bar: dropping bar with invalid volume=%r", vol
        )
        return None

    return bar


def validate_ohlcv_arrays(
    timestamps: List,
    opens: List,
    highs: List,
    lows: List,
    closes: List,
    volumes: List,
) -> Tuple[bool, str]:
    """Validate parallel OHLCV arrays for consistency.

    Checks:
    - All six arrays have the same length.
    - Each non-None bar passes sanitize_price_bar validation.

    Returns (True, '') on success or (False, reason) on first failure.
    """
    lengths = {
        'timestamps': len(timestamps),
        'opens': len(opens),
        'highs': len(highs),
        'lows': len(lows),
        'closes': len(closes),
        'volumes': len(volumes),
    }
    unique_lengths = set(lengths.values())
    if len(unique_lengths) > 1:
        return False, f"Array length mismatch: {lengths}"

    n = lengths['timestamps']
    for i in range(n):
        c = closes[i]
        if c is None:
            # Missing/halted bars are acceptable — skip validation for this index
            continue

        bar = {
            'timestamp': timestamps[i],
            'open': opens[i],
            'high': highs[i],
            'low': lows[i],
            'close': c,
            'volume': volumes[i],
        }
        if sanitize_price_bar(bar) is None:
            return False, f"Invalid bar at index {i}: {bar}"

    return True, ''
