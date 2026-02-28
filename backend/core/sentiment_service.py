```python
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
from backend.database import db_session

logger = logging.getLogger(__name__)

SENTIMENT_CACHE_TTL_SECONDS = 900  # 15 minutes

NEWS_LOOKBACK_HOURS = 24
REDDIT_LOOKBACK_HOURS = 6

BULLISH_THRESHOLD = 0.6
BEARISH_THRESHOLD = 0.4

NEWS_BULLISH_MIN = 0.1
NEWS_BEARISH_MAX = -0.1


def _score_to_label(score: float) -> str:
    if score >= BULLISH_THRESHOLD:
        return 'bullish'
    if score <= BEARISH_THRESHOLD:
        return 'bearish'
    return 'neutral'


def _get_news_signals(ticker: str, conn: sqlite3.Connection) -> dict:
    cutoff = (datetime.utcnow() - timedelta(hours=NEWS_LOOKBACK_HOURS)).isoformat()
    counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
    try:
        rows = conn.execute(
            "SELECT sentiment_score FROM news "
            "WHERE ticker = ? AND sentiment_score IS NOT NULL AND created_at >= ?",
            (ticker.upper(), cutoff),
        ).fetchall()
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


def _get_reddit_signals(ticker: str, conn: sqlite3.Connection) -> dict:
    cutoff = (datetime.utcnow() - timedelta(hours=REDDIT_LOOKBACK_HOURS)).isoformat()
    counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
    try:
        rows = conn.execute(
            "SELECT output_data FROM agent_runs "
            "WHERE agent_name = 'investigator' AND status = 'completed' "
            "  AND input_data LIKE '%reddit_scan%' AND completed_at >= ? "
            "ORDER BY completed_at DESC LIMIT 10",
            (cutoff,),
        ).fetchall()
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
        items = data if isinstance(data, list) else data.get('trending', [])
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get('ticker', '').upper() != ticker_upper:
                continue
            sentiment = item.get('sentiment', 'unknown').lower()
            weight = max(1, int(item.get('mentions', 1)))
            if sentiment == 'bullish':
                counts['bullish'] += weight
            elif sentiment == 'bearish':
                counts['bearish'] += weight
            else:
                counts['neutral'] += weight
    return counts


def _compute_sentiment(ticker: str, conn: sqlite3.Connection) -> dict:
    news_counts = _get_news_signals(ticker, conn)
    reddit_counts = _get_reddit_signals(ticker, conn)
    news_total = sum(news_counts.values())
    reddit_total = sum(reddit_counts.values())
    total = news_total + reddit_total
    sources = {'news': news_total, 'reddit': reddit_total}
    if total == 0:
        return {'ticker': ticker.upper(), 'score': None, 'label': 'neutral',
                'signal_count': 0, 'sources': sources}
    bullish = news_counts['bullish'] + reddit_counts['bullish']
    score = round(bullish / total, 4)
    return {'ticker': ticker.upper(), 'score': score,
            'label': _score_to_label(score), 'signal_count': total, 'sources': sources}


def invalidate_ticker(ticker: str, db_path: str | None = None) -> None:
    ticker = ticker.upper()
    try:
        with db_session(db_path) as conn:
            conn.execute("DELETE FROM sentiment_cache WHERE ticker = ?", (ticker,))
        logger.debug("Sentiment cache invalidated for %s", ticker)
    except Exception as exc:
        logger.warning("Cache invalidation failed for %s: %s", ticker, exc)


def get_sentiment(ticker: str, db_path: str | None = None) -> dict:
    ticker = ticker.upper()
    now = datetime.utcnow()
    cutoff = (now - timedelta(seconds=SENTIMENT_CACHE_TTL_SECONDS)).isoformat()

    try:
        with db_session(db_path) as conn:
            row = conn.execute(
                "SELECT * FROM sentiment_cache WHERE ticker = ?", (ticker,)
            ).fetchone()
        if row and row['updated_at'] >= cutoff:
            return {'ticker': ticker, 'label': row['label'], 'score': row['score'],
                    'signal_count': row['signal_count'],
                    'sources': json.loads(row['sources']),
                    'updated_at': row['updated_at'] + 'Z', 'stale': False}
    except Exception as exc:
        logger.debug("Cache read failed for %s: %s", ticker, exc)

    updated_at_stored = now.isoformat()
    result: dict = {'ticker': ticker, 'score': None, 'label': 'neutral',
                    'signal_count': 0, 'sources': {'news': 0, 'reddit': 0}}
    try:
        with db_session(db_path) as conn:
            result = _compute_sentiment(ticker, conn)
            if result['signal_count'] > 0:
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
                    (ticker, result['score'], result['label'],
                     result['signal_count'], json.dumps(result['sources']),
                     updated_at_stored),
                )
    except Exception as exc:
        logger.warning("Sentiment compute/cache failed for %s: %s", ticker, exc)

    result['updated_at'] = updated_at_stored + 'Z'
    result['stale'] = False
    return result
```