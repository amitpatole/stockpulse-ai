"""
Sentiment aggregation job.

Schedule: 5:00 PM ET daily (weekdays after market close)
Task: Aggregate sentiment scores from news articles for all stocks
Output: Update sentiment scores in ai_ratings table
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from backend.config import Config
from backend.jobs._helpers import (
    _get_watchlist,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'sentiment_aggregation'
JOB_NAME = 'Sentiment Aggregation'


def run_sentiment_aggregation() -> None:
    """Aggregate sentiment scores from news articles.

    Steps:
        1. Load active stocks from watchlist.
        2. For each stock, query news articles from the past 24 hours.
        3. Calculate weighted average sentiment score.
        4. Classify sentiment (bullish, neutral, bearish).
        5. Update ai_ratings table with aggregated sentiment.
        6. Log summary of sentiment updates.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist]

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No stocks in watchlist -- skipping sentiment aggregation.'
            return

        updated_count = 0
        failed_count = 0
        errors: Dict[str, str] = {}

        for ticker in tickers:
            try:
                # ---- 1. Fetch recent news articles ----
                articles = _fetch_recent_news(ticker, hours=24)

                if not articles:
                    logger.debug(f"No recent news for {ticker}")
                    continue

                # ---- 2. Calculate aggregated sentiment ----
                sentiment_score, sentiment_label = _aggregate_sentiment(articles)

                # ---- 3. Update database ----
                if _update_sentiment_in_ratings(ticker, sentiment_score, sentiment_label):
                    updated_count += 1
                    logger.debug(f"Updated sentiment for {ticker}: {sentiment_label}")
                else:
                    failed_count += 1
                    errors[ticker] = 'Failed to update database'

            except Exception as exc:
                failed_count += 1
                errors[ticker] = str(exc)
                logger.error(f"Error processing sentiment for {ticker}: {exc}", exc_info=False)

        ctx['result_summary'] = (
            f"Updated sentiment for {updated_count}/{len(tickers)} stocks. "
            f"{failed_count} failed."
        )

        logger.info(
            "[SENTIMENT] Updated=%d, Failed=%d, Total=%d",
            updated_count, failed_count, len(tickers),
        )


def _fetch_recent_news(ticker: str, hours: int = 24) -> list:
    """Fetch recent news articles for a stock.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol
    hours : int
        Number of hours of recent news to fetch

    Returns
    -------
    list
        List of article dicts with sentiment_score, or empty list if none found
    """
    articles = []

    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        # Calculate cutoff timestamp
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()

        # Query news articles for this ticker from past N hours
        rows = conn.execute(
            """SELECT id, title, description, sentiment_score, engagement_score
               FROM news
               WHERE ticker = ? AND created_at > ?
               ORDER BY created_at DESC""",
            (ticker, cutoff_iso),
        ).fetchall()

        articles = [dict(r) for r in rows]
        conn.close()

    except Exception as exc:
        logger.error(f"Failed to fetch news for {ticker}: {exc}")

    return articles


def _aggregate_sentiment(articles: list) -> tuple:
    """Aggregate sentiment scores from multiple articles.

    Uses weighted average where engagement_score is the weight.
    Classifies into: bullish (>0.3), bearish (<-0.3), neutral (rest).

    Parameters
    ----------
    articles : list
        List of article dicts with sentiment_score, engagement_score

    Returns
    -------
    tuple
        (sentiment_score: float, sentiment_label: str)
    """
    if not articles:
        return 0.0, 'neutral'

    total_weight = 0.0
    weighted_score = 0.0

    for article in articles:
        score = article.get('sentiment_score')
        weight = article.get('engagement_score', 1.0)

        if score is not None and weight is not None:
            weighted_score += score * weight
            total_weight += weight

    # Calculate weighted average
    if total_weight > 0:
        avg_score = weighted_score / total_weight
    else:
        avg_score = 0.0

    # Classify sentiment
    if avg_score > 0.3:
        label = 'bullish'
    elif avg_score < -0.3:
        label = 'bearish'
    else:
        label = 'neutral'

    return round(avg_score, 3), label


def _update_sentiment_in_ratings(
    ticker: str,
    sentiment_score: float,
    sentiment_label: str,
) -> bool:
    """Update sentiment scores in ai_ratings table.

    Parameters
    ----------
    ticker : str
        Stock ticker
    sentiment_score : float
        Aggregated sentiment score (-1.0 to 1.0)
    sentiment_label : str
        Sentiment classification (bullish, neutral, bearish)

    Returns
    -------
    bool
        True if update succeeded, False otherwise
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        # Check if record exists
        existing = conn.execute(
            "SELECT id FROM ai_ratings WHERE ticker = ?",
            (ticker,),
        ).fetchone()

        if existing:
            # Update existing record
            conn.execute(
                """UPDATE ai_ratings
                   SET sentiment_score = ?,
                       sentiment_label = ?,
                       updated_at = ?
                   WHERE ticker = ?""",
                (sentiment_score, sentiment_label, datetime.utcnow().isoformat(), ticker),
            )
        else:
            # Insert new record
            conn.execute(
                """INSERT INTO ai_ratings
                   (ticker, rating, score, confidence, sentiment_score, sentiment_label, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (ticker, 'HOLD', 0.0, 0.0, sentiment_score, sentiment_label,
                 datetime.utcnow().isoformat()),
            )

        conn.commit()
        conn.close()
        return True

    except Exception as exc:
        logger.error(f"Failed to update sentiment for {ticker}: {exc}")
        return False
