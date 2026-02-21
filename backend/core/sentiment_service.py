"""
TickerPulse AI v3.0 - Sentiment Service

Aggregates social/news sentiment signals for stock tickers into a single
0.0–1.0 bullish-proportion score, cached in SQLite with a 15-minute TTL.

Sources:
  - news table  : articles with NLP sentiment_score (-1 to 1)
  - agent_runs  : recent investigator runs from the Reddit scanner job
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta

from backend.config import Config

logger = logging.getLogger(__name__)

SENTIMENT_CACHE_TTL_SECONDS = 900  # 15 minutes

# Lookback windows for signal collection
NEWS_LOOKBACK_HOURS = 24
REDDIT_LOOKBACK_HOURS = 6

# Label thresholds (applied to 0–1 score)
BULLISH_THRESHOLD = 0.6
BEARISH_THRESHOLD = 0.4

# News score thresholds for signal classification
NEWS_BULLISH_MIN = 0.1
NEWS_BEARISH_MAX = -0.1


def _score_to_label(score: float) -> str:
    """Map a 0–1 bullish proportion to 'bullish' | 'neutral' | 'bearish'."""
    if score >= BULLISH_THRESHOLD:
        return 'bullish'
    if score <= BEARISH_THRESHOLD:
        return 'bearish'
    return 'neutral'


def _get_news_signals(ticker: str, db_path: str) -> dict:
    """Return news sentiment signal counts for *ticker*.

    Returns a dict with keys: bullish, bearish, neutral (integer counts).
    """
    cutoff = (datetime.utcnow() - timedelta(hours=NEWS_LOOKBACK_HOURS)).isoformat()
    counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT sentiment_score FROM news
            WHERE ticker = ? AND sentiment_score IS NOT NULL AND created_at >= ?
            """,
            (ticker.upper(), cutoff),
        ).fetchall()
        conn.close()
    except Exception as exc:
        logger.debug("News query failed for %s: %s", ticker, exc)
        return counts

    for row in rows:
        score = row['sentiment_score']
        if score > NEWS_BULLISH_MIN:
            counts['bullish'] += 1
        elif score < NEWS_BEARISH_MAX:
            counts['bearish'] += 1
        else:
            counts['neutral'] += 1
    return counts


def _get_reddit_signals(ticker: str, db_path: str) -> dict:
    """Return Reddit sentiment signal counts for *ticker*.

    Parses recent investigator agent-run outputs from the Reddit scanner job.
    Returns a dict with keys: bullish, bearish, neutral (integer counts).
    """
    cutoff = (datetime.utcnow() - timedelta(hours=REDDIT_LOOKBACK_HOURS)).isoformat()
    counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT output_data FROM agent_runs
            WHERE agent_name = 'investigator'
              AND status = 'completed'
              AND input_data LIKE '%reddit_scan%'
              AND completed_at >= ?
            ORDER BY completed_at DESC
            LIMIT 10
            """,
            (cutoff,),
        ).fetchall()
        conn.close()
    except Exception as exc:
        logger.debug("Reddit agent_runs query failed for %s: %s", ticker, exc)
        return counts

    ticker_upper = ticker.upper()
    for row in rows:
        output = row['output_data']
        if not output:
            continue
        try:
            data = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            continue

        # Handle list of trending items or {"trending": [...]} wrapper
        items = data if isinstance(data, list) else data.get('trending', [])
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get('ticker', '').upper() != ticker_upper:
                continue
            sentiment = item.get('sentiment', 'unknown').lower()
            # Weight by mention count when available
            weight = max(1, int(item.get('mentions', 1)))
            if sentiment == 'bullish':
                counts['bullish'] += weight
            elif sentiment == 'bearish':
                counts['bearish'] += weight
            else:
                counts['neutral'] += weight
    return counts


def _compute_sentiment(ticker: str, db_path: str) -> dict:
    """Aggregate news + Reddit signals into a raw (uncached) sentiment dict."""
    news_counts = _get_news_signals(ticker, db_path)
    reddit_counts = _get_reddit_signals(ticker, db_path)

    news_total = sum(news_counts.values())
    reddit_total = sum(reddit_counts.values())
    total = news_total + reddit_total

    sources = {'news': news_total, 'reddit': reddit_total}

    if total == 0:
        return {
            'ticker': ticker.upper(),
            'score': None,
            'label': 'neutral',
            'signal_count': 0,
            'sources': sources,
        }

    bullish = news_counts['bullish'] + reddit_counts['bullish']
    score = round(bullish / total, 4)
    return {
        'ticker': ticker.upper(),
        'score': score,
        'label': _score_to_label(score),
        'signal_count': total,
        'sources': sources,
    }


def get_sentiment(ticker: str, db_path: str | None = None) -> dict:
    """Return cached or freshly-computed sentiment for *ticker*.

    Cache TTL is ``SENTIMENT_CACHE_TTL_SECONDS`` (15 min).

    Always returns a dict with keys:
        ticker, label, score, signal_count, sources, updated_at, stale.
    """
    db_path = db_path or Config.DB_PATH
    ticker = ticker.upper()
    now = datetime.utcnow()
    cutoff = (now - timedelta(seconds=SENTIMENT_CACHE_TTL_SECONDS)).isoformat()

    # --- Try cache ---
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM sentiment_cache WHERE ticker = ?", (ticker,)
        ).fetchone()
        conn.close()

        if row and row['updated_at'] >= cutoff:
            return {
                'ticker': ticker,
                'label': row['label'],
                'score': row['score'],
                'signal_count': row['signal_count'],
                'sources': json.loads(row['sources']),
                'updated_at': row['updated_at'] + 'Z',
                'stale': False,
            }
    except Exception as exc:
        logger.debug("Cache read failed for %s: %s", ticker, exc)

    # --- Compute fresh ---
    result = _compute_sentiment(ticker, db_path)
    updated_at_stored = now.isoformat()

    # Only cache when there are actual signals (score column is NOT NULL)
    if result['signal_count'] > 0:
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                INSERT INTO sentiment_cache
                    (ticker, score, label, signal_count, sources, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    score        = excluded.score,
                    label        = excluded.label,
                    signal_count = excluded.signal_count,
                    sources      = excluded.sources,
                    updated_at   = excluded.updated_at
                """,
                (
                    ticker,
                    result['score'],
                    result['label'],
                    result['signal_count'],
                    json.dumps(result['sources']),
                    updated_at_stored,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("Cache write failed for %s: %s", ticker, exc)

    result['updated_at'] = updated_at_stored + 'Z'
    result['stale'] = False
    return result
