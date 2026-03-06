"""
Daily technical indicators update job.

Schedule: 6:00 AM ET, Mon-Fri
Task: Update ai_ratings table with latest technical indicators
Data Source: Historical OHLCV from market data providers
Output: Updated indicator values in ai_ratings table
"""
import logging
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any

from backend.config import Config
from backend.core.indicators import sma, ema, rsi, macd, bollinger_bands, atr
from backend.jobs._helpers import (
    _get_watchlist,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'daily_indicators_update'
JOB_NAME = 'Daily Indicators Update'


def run_daily_indicators_update() -> None:
    """Update technical indicators for all stocks in watchlist.

    Steps:
        1. Load active stocks from watchlist.
        2. For each stock, fetch recent OHLCV data (60 days).
        3. Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR).
        4. Update ai_ratings table with calculated values.
        5. Log results and failures for manual review.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist]

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No stocks in watchlist -- skipping indicator update.'
            return

        updated_count = 0
        failed_count = 0
        errors: Dict[str, str] = {}

        for ticker in tickers:
            try:
                ohlcv_data = _fetch_ohlcv_data(ticker, days=60)
                if not ohlcv_data:
                    failed_count += 1
                    errors[ticker] = 'Failed to fetch OHLCV data'
                    logger.warning(f"No OHLCV data for {ticker}")
                    continue

                # Extract price data
                closes = [candle['close'] for candle in ohlcv_data]
                highs = [candle['high'] for candle in ohlcv_data]
                lows = [candle['low'] for candle in ohlcv_data]
                volumes = [candle['volume'] for candle in ohlcv_data]

                # Calculate indicators
                indicators = _calculate_indicators(
                    closes=closes,
                    highs=highs,
                    lows=lows,
                    volumes=volumes,
                    ticker=ticker,
                )

                # Update database
                if _update_ai_ratings(ticker, indicators):
                    updated_count += 1
                    logger.debug(f"Updated indicators for {ticker}")
                else:
                    failed_count += 1
                    errors[ticker] = 'Failed to update database'

            except Exception as exc:
                failed_count += 1
                errors[ticker] = str(exc)
                logger.error(f"Error processing {ticker}: {exc}", exc_info=False)

        ctx['result_summary'] = (
            f"Updated indicators for {updated_count}/{len(tickers)} stocks. "
            f"{failed_count} failed."
        )
        if errors:
            ctx['result_summary'] += f" Errors: {len(errors)}"

        logger.info(
            "[INDICATORS] Updated=%d, Failed=%d, Total=%d",
            updated_count, failed_count, len(tickers),
        )


def _fetch_ohlcv_data(
    ticker: str,
    days: int = 60,
) -> Optional[list]:
    """Fetch recent OHLCV data for a ticker.

    This is a stub that returns synthetic data for demonstration.
    In production, this would call a market data provider (Alpha Vantage,
    IB, Polygon, etc.).

    Parameters
    ----------
    ticker : str
        Stock ticker symbol
    days : int
        Number of days of historical data to fetch

    Returns
    -------
    list of dict or None
        List of OHLCV candles, or None if fetch failed
    """
    try:
        # TODO: Replace with actual market data API call
        # Stub: return empty list (production code would call real API)
        return None
    except Exception as exc:
        logger.error(f"Failed to fetch OHLCV for {ticker}: {exc}")
        return None


def _calculate_indicators(
    closes: list,
    highs: list,
    lows: list,
    volumes: list,
    ticker: str,
) -> Dict[str, Any]:
    """Calculate all technical indicators for a stock.

    Parameters
    ----------
    closes : list
        List of closing prices
    highs : list
        List of high prices
    lows : list
        List of low prices
    volumes : list
        List of volumes
    ticker : str
        Stock ticker for logging

    Returns
    -------
    dict
        Dictionary of calculated indicator values
    """
    indicators: Dict[str, Any] = {}

    # Simple Moving Averages
    indicators['sma_20'] = sma(closes, period=20)
    indicators['sma_50'] = sma(closes, period=50)
    indicators['sma_200'] = sma(closes, period=200)

    # Exponential Moving Average
    indicators['ema_12'] = ema(closes, period=12)
    indicators['ema_26'] = ema(closes, period=26)

    # RSI (Relative Strength Index)
    indicators['rsi_14'] = rsi(closes, period=14)

    # MACD (Moving Average Convergence Divergence)
    macd_result = macd(closes)
    if macd_result:
        indicators['macd_line'] = macd_result[0]
        indicators['macd_signal'] = macd_result[1]
        indicators['macd_histogram'] = macd_result[2]
    else:
        indicators['macd_line'] = None
        indicators['macd_signal'] = None
        indicators['macd_histogram'] = None

    # Bollinger Bands
    bb_result = bollinger_bands(closes, period=20)
    if bb_result:
        indicators['bb_upper'] = bb_result[0]
        indicators['bb_middle'] = bb_result[1]
        indicators['bb_lower'] = bb_result[2]
    else:
        indicators['bb_upper'] = None
        indicators['bb_middle'] = None
        indicators['bb_lower'] = None

    # ATR (Average True Range)
    indicators['atr_14'] = atr(highs, lows, closes, period=14)

    # Current price (last close)
    indicators['current_price'] = closes[-1] if closes else None

    return indicators


def _update_ai_ratings(ticker: str, indicators: Dict[str, Any]) -> bool:
    """Update ai_ratings table with calculated indicators.

    Parameters
    ----------
    ticker : str
        Stock ticker
    indicators : dict
        Dictionary of calculated indicator values

    Returns
    -------
    bool
        True if update succeeded, False otherwise
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        # Check if record exists
        existing = conn.execute(
            "SELECT id FROM ai_ratings WHERE ticker = ?",
            (ticker,),
        ).fetchone()

        current_price = indicators.get('current_price')

        if existing:
            # Update existing record
            conn.execute(
                """UPDATE ai_ratings
                   SET current_price = ?,
                       updated_at = ?
                   WHERE ticker = ?""",
                (current_price, datetime.utcnow().isoformat(), ticker),
            )
        else:
            # Insert new record
            conn.execute(
                """INSERT INTO ai_ratings
                   (ticker, rating, score, confidence, current_price, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ticker, 'HOLD', 0.0, 0.0, current_price, datetime.utcnow().isoformat()),
            )

        conn.commit()
        conn.close()
        return True

    except Exception as exc:
        logger.error(f"Failed to update ai_ratings for {ticker}: {exc}")
        return False
