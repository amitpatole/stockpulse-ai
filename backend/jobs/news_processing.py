"""
News processing job.

Schedule: Every 2 hours during market hours + 1 hour after close
Task: Fetch, validate, and process news articles
Output: Insert news records into database with sentiment analysis
"""
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.config import Config
from backend.jobs._helpers import (
    _get_watchlist,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'news_processing'
JOB_NAME = 'News Processing'


def run_news_processing() -> None:
    """Fetch and process news articles for monitored stocks.

    Steps:
        1. Load active stocks from watchlist.
        2. For each stock, fetch latest news from news sources.
        3. Validate article data (title, URL, date).
        4. Check for duplicates (by URL).
        5. Perform sentiment analysis on article titles/descriptions.
        6. Insert valid articles into news table.
        7. Log summary of processed articles.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist]

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No stocks in watchlist -- skipping news processing.'
            return

        articles_fetched = 0
        articles_inserted = 0
        duplicates_found = 0
        failed_count = 0
        errors: Dict[str, str] = {}

        for ticker in tickers:
            try:
                # ---- 1. Fetch news for this ticker ----
                articles = _fetch_news_for_ticker(ticker)

                if not articles:
                    logger.debug(f"No new articles for {ticker}")
                    continue

                articles_fetched += len(articles)

                # ---- 2-5. Process articles ----
                for article in articles:
                    try:
                        # Validate article
                        if not _validate_article(article):
                            logger.debug(f"Skipped invalid article for {ticker}")
                            continue

                        # Check for duplicates
                        if _is_duplicate(article['url']):
                            duplicates_found += 1
                            logger.debug(f"Duplicate article for {ticker}: {article['url']}")
                            continue

                        # Perform sentiment analysis
                        sentiment_score = _analyze_sentiment(article)

                        # Insert into database
                        if _insert_news_article(ticker, article, sentiment_score):
                            articles_inserted += 1
                        else:
                            logger.warning(f"Failed to insert article for {ticker}")

                    except Exception as exc:
                        logger.error(f"Error processing article for {ticker}: {exc}")

            except Exception as exc:
                failed_count += 1
                errors[ticker] = str(exc)
                logger.error(f"Error processing news for {ticker}: {exc}", exc_info=False)

        ctx['result_summary'] = (
            f"Fetched {articles_fetched} articles. "
            f"Inserted {articles_inserted}, duplicates {duplicates_found}, failed {failed_count}."
        )

        logger.info(
            "[NEWS] Fetched=%d, Inserted=%d, Duplicates=%d, Failed=%d",
            articles_fetched, articles_inserted, duplicates_found, failed_count,
        )


def _fetch_news_for_ticker(ticker: str) -> List[Dict[str, Any]]:
    """Fetch latest news articles for a ticker.

    This is a stub that returns empty list for demonstration.
    In production, would call actual news API (Alpha Vantage, Finnhub,
    NewsAPI, etc.).

    Parameters
    ----------
    ticker : str
        Stock ticker symbol

    Returns
    -------
    list
        List of article dicts with keys: title, description, url,
        source, published_date
    """
    try:
        # TODO: Replace with actual news API call
        # Stub: return empty list (production code would call real API)
        return []

    except Exception as exc:
        logger.error(f"Failed to fetch news for {ticker}: {exc}")
        return []


def _validate_article(article: Dict[str, Any]) -> bool:
    """Validate article data structure.

    Parameters
    ----------
    article : dict
        Article data

    Returns
    -------
    bool
        True if article is valid, False otherwise
    """
    required_fields = ['title', 'url']

    for field in required_fields:
        if field not in article or not article[field]:
            return False

    # Validate URL
    if not isinstance(article['url'], str) or len(article['url']) < 10:
        return False

    return True


def _is_duplicate(url: str) -> bool:
    """Check if article URL already exists in database.

    Parameters
    ----------
    url : str
        Article URL

    Returns
    -------
    bool
        True if duplicate exists, False otherwise
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        result = conn.execute(
            "SELECT id FROM news WHERE url = ?",
            (url,),
        ).fetchone()

        conn.close()
        return result is not None

    except Exception as exc:
        logger.error(f"Failed to check duplicate for URL {url}: {exc}")
        return False


def _analyze_sentiment(article: Dict[str, Any]) -> float:
    """Analyze sentiment of article title and description.

    This is a stub that returns 0.0 (neutral).
    In production, would call sentiment analysis API or ML model.

    Parameters
    ----------
    article : dict
        Article data with title and description

    Returns
    -------
    float
        Sentiment score (-1.0 to 1.0), where:
        - > 0: positive/bullish
        - 0: neutral
        - < 0: negative/bearish
    """
    try:
        # TODO: Replace with actual sentiment analysis
        # Stub: return neutral sentiment (production would call ML model)
        return 0.0

    except Exception as exc:
        logger.error(f"Failed to analyze sentiment: {exc}")
        return 0.0


def _insert_news_article(
    ticker: str,
    article: Dict[str, Any],
    sentiment_score: float,
) -> bool:
    """Insert article into news table.

    Parameters
    ----------
    ticker : str
        Stock ticker
    article : dict
        Article data
    sentiment_score : float
        Sentiment analysis result

    Returns
    -------
    bool
        True if insert succeeded, False otherwise
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        conn.execute(
            """INSERT INTO news
               (ticker, title, description, url, source, published_date, sentiment_score)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                ticker,
                article.get('title', '')[:500],
                article.get('description', '')[:2000],
                article.get('url', '')[:2000],
                article.get('source', '')[:200],
                article.get('published_date'),
                sentiment_score,
            ),
        )

        conn.commit()
        conn.close()
        return True

    except Exception as exc:
        logger.error(f"Failed to insert news article for {ticker}: {exc}")
        return False
