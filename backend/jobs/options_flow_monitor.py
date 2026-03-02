```python
"""
TickerPulse AI - Options Flow Monitor Job
Background job that polls options data and detects anomalies.
Runs every 60 seconds during market hours.
"""

import logging
from typing import List

from backend.config import Config
from backend.database import db_session
from backend.data_providers.tradingview_options import TradingViewOptionsProvider
from backend.core.options_analyzer import OptionsAnalyzer, AnomalyDetectionResult
from backend.scheduler import scheduler_manager

logger = logging.getLogger(__name__)


def run_options_flow_monitor() -> None:
    """Monitor options flow and detect anomalies.

    This job:
    1. Initializes a data provider (TradingView)
    2. Initializes the analyzer
    3. Gets list of watched tickers from database
    4. Analyzes each for anomalies
    5. Stores results in options_flows table
    6. Broadcasts alerts via WebSocket (if alert matches subscription)
    """
    try:
        # Only run during market hours
        if not scheduler_manager.is_market_hours('US'):
            logger.debug("Options monitor skipped: market hours not active")
            return

        logger.info("Starting options flow monitor job")

        # Initialize provider and analyzer
        provider = TradingViewOptionsProvider(api_key=None)  # None = mock mode
        analyzer = OptionsAnalyzer(provider)

        # Get watched tickers (from stocks table)
        watched_tickers = _get_watched_tickers()
        if not watched_tickers:
            logger.debug("No tickers to analyze")
            return

        logger.info(f"Analyzing {len(watched_tickers)} tickers for options flow")

        # Analyze each ticker
        for ticker in watched_tickers:
            try:
                anomalies = analyzer.analyze_ticker(ticker)
                
                if anomalies:
                    logger.info(f"Found {len(anomalies)} anomalies for {ticker}")
                    _store_anomalies(ticker, anomalies)
                    _trigger_alerts(ticker, anomalies)
            except Exception as exc:
                logger.error(f"Error analyzing {ticker}: {exc}")

        logger.info("Options flow monitor job completed")

    except Exception as exc:
        logger.error(f"Options flow monitor job failed: {exc}")


def _get_watched_tickers() -> List[str]:
    """Get list of tickers to monitor.

    Returns
    -------
    List[str]
        List of ticker symbols.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT ticker FROM stocks
                WHERE ticker IS NOT NULL AND ticker != ''
                ORDER BY ticker
                LIMIT 50
            """)
            rows = cursor.fetchall()
            return [row['ticker'] for row in rows]
    except Exception as exc:
        logger.error(f"Failed to get watched tickers: {exc}")
        return []


def _store_anomalies(ticker: str, anomalies: List[AnomalyDetectionResult]) -> None:
    """Store detected anomalies in the database.

    Parameters
    ----------
    ticker : str
        Stock ticker.
    anomalies : List[AnomalyDetectionResult]
        List of anomalies to store.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            for anomaly in anomalies:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO options_flows
                        (ticker, contract, option_type, strike, expiration,
                         volume, open_interest, bid_ask_spread, iv_percentile,
                         flow_type, anomaly_score, is_alert)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker,
                        anomaly.contract.contract,
                        anomaly.contract.option_type,
                        anomaly.contract.strike,
                        anomaly.contract.expiration,
                        anomaly.contract.volume,
                        anomaly.contract.open_interest,
                        anomaly.contract.bid_ask_spread,
                        anomaly.contract.iv_percentile,
                        anomaly.flow_type,
                        anomaly.anomaly_score,
                        1 if anomaly.anomaly_score >= 70 else 0,
                    ))
                except Exception as exc:
                    logger.warning(f"Failed to store anomaly {anomaly.contract.contract}: {exc}")

            conn.commit()
    except Exception as exc:
        logger.error(f"Failed to store anomalies for {ticker}: {exc}")


def _trigger_alerts(ticker: str, anomalies: List[AnomalyDetectionResult]) -> None:
    """Trigger alerts for anomalies that match user subscriptions.

    Parameters
    ----------
    ticker : str
        Stock ticker.
    anomalies : List[AnomalyDetectionResult]
        List of anomalies detected.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # Get subscriptions that match this ticker
            cursor.execute("""
                SELECT id, user_id, ticker, flow_type, min_anomaly_score
                FROM alert_subscriptions
                WHERE is_active = 1
                AND (ticker IS NULL OR ticker = ?)
            """, (ticker,))
            subscriptions = cursor.fetchall()

            for subscription in subscriptions:
                for anomaly in anomalies:
                    # Check if anomaly matches subscription criteria
                    flow_type_match = (
                        subscription['flow_type'] is None or 
                        subscription['flow_type'] == anomaly.flow_type
                    )
                    score_match = anomaly.anomaly_score >= subscription['min_anomaly_score']

                    if flow_type_match and score_match:
                        # In production, send WebSocket notification here
                        # For now, just log it
                        logger.info(
                            f"Alert triggered for user {subscription['user_id']}: "
                            f"{anomaly.flow_type} on {ticker} (score: {anomaly.anomaly_score:.1f})"
                        )

    except Exception as exc:
        logger.error(f"Failed to trigger alerts for {ticker}: {exc}")
```