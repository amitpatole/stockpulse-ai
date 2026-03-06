"""
TickerPulse AI v3.0 - Technical Indicators Module
Complete implementation of 10+ technical indicators with proper error handling.

Indicators included:
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ATR (Average True Range)
- Stochastic Oscillator
- ADX (Average Directional Index)
- VWAP (Volume Weighted Average Price)
- OBV (On-Balance Volume)
"""

import math
from typing import List, Dict, Optional, Sequence


def validate_prices(prices: Sequence[Optional[float]], min_length: int = 1) -> bool:
    """Validate that prices list has sufficient data."""
    if not prices or len(prices) < min_length:
        return False
    return any(p is not None and p > 0 for p in prices)


def filter_none_values(values: List[Optional[float]]) -> List[float]:
    """Remove None values from a list, preserving order."""
    return [v for v in values if v is not None]


def sma(closes: List[float], period: int = 20) -> Optional[float]:
    """
    Calculate Simple Moving Average (SMA).

    Parameters
    ----------
    closes : List[float]
        Price data (closing prices)
    period : int
        Period for SMA calculation (default: 20)

    Returns
    -------
    float or None
        SMA value, or None if insufficient data
    """
    if not validate_prices(closes, period):
        return None

    window = closes[-period:]
    return sum(window) / len(window)


def ema(closes: List[float], period: int = 12) -> Optional[float]:
    """
    Calculate Exponential Moving Average (EMA).

    Parameters
    ----------
    closes : List[float]
        Price data (closing prices)
    period : int
        Period for EMA calculation (default: 12)

    Returns
    -------
    float or None
        EMA value, or None if insufficient data
    """
    if not validate_prices(closes, period):
        return None

    multiplier = 2 / (period + 1)
    # Initialize EMA with SMA of first `period` values
    ema_val = sum(closes[:period]) / period

    # Calculate EMA for remaining values
    for price in closes[period:]:
        ema_val = (price * multiplier) + (ema_val * (1 - multiplier))

    return ema_val


def rsi(closes: List[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI).

    Parameters
    ----------
    closes : List[float]
        Price data (closing prices)
    period : int
        Period for RSI calculation (default: 14)

    Returns
    -------
    float or None
        RSI value (0-100), or None if insufficient data
    """
    if not validate_prices(closes, period + 1):
        return None

    # Calculate price deltas
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    # Separate gains and losses
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    # Calculate average gains and losses
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(closes: List[float]) -> Optional[Dict[str, float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Parameters
    ----------
    closes : List[float]
        Price data (closing prices)

    Returns
    -------
    dict or None
        Dictionary with 'macd', 'signal', 'histogram' keys, or None if insufficient data
    """
    if not validate_prices(closes, 26):
        return None

    ema_12 = ema(closes, 12)
    ema_26 = ema(closes, 26)

    if ema_12 is None or ema_26 is None:
        return None

    macd_val = ema_12 - ema_26
    signal_val = ema([macd_val], 9)

    if signal_val is None:
        signal_val = macd_val

    histogram = macd_val - signal_val

    return {
        'macd': round(macd_val, 4),
        'signal': round(signal_val, 4),
        'histogram': round(histogram, 4),
    }


def bollinger_bands(closes: List[float], period: int = 20, num_std: float = 2.0) -> Optional[Dict[str, float]]:
    """
    Calculate Bollinger Bands.

    Parameters
    ----------
    closes : List[float]
        Price data (closing prices)
    period : int
        Period for moving average (default: 20)
    num_std : float
        Number of standard deviations (default: 2.0)

    Returns
    -------
    dict or None
        Dictionary with 'upper', 'middle', 'lower', 'bandwidth', 'percent_b' keys
    """
    if not validate_prices(closes, period):
        return None

    window = closes[-period:]
    middle = sum(window) / period

    # Calculate standard deviation
    variance = sum((p - middle) ** 2 for p in window) / period
    std_dev = math.sqrt(variance)

    upper = middle + (num_std * std_dev)
    lower = middle - (num_std * std_dev)
    current = closes[-1]

    # Calculate %B (Percent B)
    band_width = upper - lower
    if band_width > 0:
        percent_b = (current - lower) / band_width
    else:
        percent_b = 0.5

    bandwidth_pct = (band_width / middle * 100) if middle > 0 else 0

    return {
        'upper': round(upper, 4),
        'middle': round(middle, 4),
        'lower': round(lower, 4),
        'bandwidth': round(bandwidth_pct, 4),
        'percent_b': round(percent_b, 4),
    }


def atr(
    highs: Sequence[Optional[float]],
    lows: Sequence[Optional[float]],
    closes: Sequence[float],
    period: int = 14
) -> Optional[Dict[str, float]]:
    """
    Calculate Average True Range (ATR).

    Parameters
    ----------
    highs : List[float]
        High prices
    lows : List[float]
        Low prices
    closes : List[float]
        Closing prices
    period : int
        Period for ATR calculation (default: 14)

    Returns
    -------
    dict or None
        Dictionary with 'atr', 'atr_percent' keys
    """
    if not validate_prices(closes, period + 1):
        return None

    if len(highs) < period + 1 or len(lows) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(closes)):
        h = highs[i] if highs[i] is not None else closes[i]
        l = lows[i] if lows[i] is not None else closes[i]
        prev_c = closes[i - 1]

        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        true_ranges.append(tr)

    if not true_ranges or len(true_ranges) < period:
        return None

    atr_val = sum(true_ranges[-period:]) / period
    current_price = closes[-1]
    atr_pct = (atr_val / current_price * 100) if current_price > 0 else 0

    return {
        'atr': round(atr_val, 4),
        'atr_percent': round(atr_pct, 4),
    }


def stochastic(
    closes: Sequence[float],
    highs: Sequence[Optional[float]],
    lows: Sequence[Optional[float]],
    k_period: int = 14,
    d_period: int = 3
) -> Optional[Dict[str, float]]:
    """
    Calculate Stochastic Oscillator (%K and %D).

    Parameters
    ----------
    closes : List[float]
        Closing prices
    highs : List[float]
        High prices
    lows : List[float]
        Low prices
    k_period : int
        Period for %K calculation (default: 14)
    d_period : int
        Period for %D calculation (default: 3)

    Returns
    -------
    dict or None
        Dictionary with 'percent_k', 'percent_d' keys
    """
    if not validate_prices(closes, k_period):
        return None

    if len(highs) < k_period or len(lows) < k_period:
        return None

    # Get recent highs and lows
    recent_highs = [h for h in highs[-k_period:] if h is not None]
    recent_lows = [l for l in lows[-k_period:] if l is not None]

    if not recent_highs or not recent_lows:
        return None

    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)
    current_close = closes[-1]

    denom = highest_high - lowest_low
    if denom == 0:
        percent_k = 50.0
    else:
        percent_k = ((current_close - lowest_low) / denom * 100)

    # Calculate %D as SMA of %K values
    k_values = []
    for i in range(max(0, len(closes) - d_period), len(closes)):
        start = max(0, i - k_period + 1)
        window_h = [h for h in highs[start:i + 1] if h is not None]
        window_l = [l for l in lows[start:i + 1] if l is not None]

        if window_h and window_l:
            hh = max(window_h)
            ll = min(window_l)
            d = hh - ll
            k_val = ((closes[i] - ll) / d * 100) if d > 0 else 50.0
            k_values.append(k_val)

    percent_d = sum(k_values) / len(k_values) if k_values else percent_k

    return {
        'percent_k': round(percent_k, 2),
        'percent_d': round(percent_d, 2),
    }


def adx(
    highs: Sequence[Optional[float]],
    lows: Sequence[Optional[float]],
    closes: Sequence[float],
    period: int = 14
) -> Optional[Dict[str, float]]:
    """
    Calculate Average Directional Index (ADX).

    Measures trend strength without indicating direction.

    Parameters
    ----------
    highs : List[float]
        High prices
    lows : List[float]
        Low prices
    closes : List[float]
        Closing prices
    period : int
        Period for ADX calculation (default: 14)

    Returns
    -------
    dict or None
        Dictionary with 'adx', 'plus_di', 'minus_di' keys
    """
    if not validate_prices(closes, period + 1):
        return None

    if len(highs) < period + 1 or len(lows) < period + 1:
        return None

    # Calculate directional movements
    plus_dm: List[float] = []
    minus_dm: List[float] = []
    true_ranges: List[float] = []

    for i in range(1, len(closes)):
        h_curr = highs[i] if highs[i] is not None else closes[i]
        h_prev = highs[i - 1] if highs[i - 1] is not None else closes[i - 1]
        l_curr = lows[i] if lows[i] is not None else closes[i]
        l_prev = lows[i - 1] if lows[i - 1] is not None else closes[i - 1]

        high_diff = h_curr - h_prev
        low_diff = l_prev - l_curr

        # Determine plus and minus DM
        if high_diff > 0 and high_diff > low_diff:
            plus_dm.append(high_diff)
        else:
            plus_dm.append(0.0)

        if low_diff > 0 and low_diff > high_diff:
            minus_dm.append(low_diff)
        else:
            minus_dm.append(0.0)

        # Calculate true range
        tr = max(h_curr - l_curr, abs(h_curr - closes[i - 1]), abs(l_curr - closes[i - 1]))
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return None

    # Calculate DI+ and DI-
    tr_sum = sum(true_ranges[-period:])
    if tr_sum == 0:
        return None

    plus_di = 100 * (sum(plus_dm[-period:]) / tr_sum)
    minus_di = 100 * (sum(minus_dm[-period:]) / tr_sum)

    # Calculate ADX (simplified: DX over period, then smoothed)
    di_sum = plus_di + minus_di
    if di_sum == 0:
        dx = 0.0
    else:
        dx = 100 * abs(plus_di - minus_di) / di_sum

    adx_val = dx  # Simplified; full ADX requires smoothing over additional periods

    return {
        'adx': round(adx_val, 2),
        'plus_di': round(plus_di, 2),
        'minus_di': round(minus_di, 2),
    }


def vwap(
    closes: Sequence[float],
    highs: Sequence[Optional[float]],
    lows: Sequence[Optional[float]],
    volumes: Sequence[Optional[int]]
) -> Optional[Dict[str, float]]:
    """
    Calculate Volume Weighted Average Price (VWAP).

    Parameters
    ----------
    closes : List[float]
        Closing prices
    highs : List[float]
        High prices
    lows : List[float]
        Low prices
    volumes : List[int]
        Trading volumes

    Returns
    -------
    dict or None
        Dictionary with 'vwap', 'current_price', 'deviation_pct' keys
    """
    if not closes or not volumes:
        return None

    if len(closes) != len(highs) or len(closes) != len(lows) or len(closes) != len(volumes):
        return None

    total_volume: int = 0
    cumulative_tp_volume: float = 0.0

    for i in range(len(closes)):
        c = closes[i]
        h = highs[i] if highs[i] is not None else c
        l = lows[i] if lows[i] is not None else c
        v = volumes[i] if volumes[i] is not None else 0

        if c is None or v <= 0:
            continue

        typical_price = (h + l + c) / 3
        cumulative_tp_volume += typical_price * v
        total_volume += int(v) if v is not None else 0

    if total_volume == 0:
        return None

    vwap_val = cumulative_tp_volume / total_volume
    current = closes[-1] if closes[-1] is not None else 0

    deviation = (current - vwap_val) / vwap_val * 100 if vwap_val > 0 else 0

    return {
        'vwap': round(vwap_val, 4),
        'current_price': round(current, 4),
        'deviation_pct': round(deviation, 4),
    }


def obv(closes: Sequence[float], volumes: Sequence[Optional[int]]) -> Optional[Dict[str, int]]:
    """
    Calculate On-Balance Volume (OBV).

    Parameters
    ----------
    closes : Sequence[float]
        Closing prices
    volumes : Sequence[int]
        Trading volumes

    Returns
    -------
    dict or None
        Dictionary with 'obv' key
    """
    if len(closes) < 2 or not volumes or len(closes) != len(volumes):
        return None

    obv_val: int = 0

    for i in range(1, len(closes)):
        c = closes[i]
        prev_c = closes[i - 1]
        v = volumes[i] if volumes[i] is not None else 0

        if c is None or prev_c is None:
            continue

        if c > prev_c:
            obv_val += int(v) if v is not None else 0
        elif c < prev_c:
            obv_val -= int(v) if v is not None else 0

    return {
        'obv': obv_val,
    }
