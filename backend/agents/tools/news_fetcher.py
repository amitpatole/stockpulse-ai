"""
StockPulse AI v3.0 - News Fetcher Tool (CrewAI Compatible)
Wraps the EnhancedStockNewsMonitor's fetch methods as a CrewAI tool.
Fetches from Google News, Yahoo Finance, Seeking Alpha, MarketWatch,
Benzinga, Finviz, StockTwits, and returns formatted results with sentiment.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Try to import CrewAI BaseTool; fall back to a minimal shim
# ------------------------------------------------------------------
try:
    from crewai.tools import BaseTool as _CrewAIBaseTool
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField

    CREWAI_AVAILABLE = True

    class NewsFetcherInput(_PydanticBaseModel):
        """Input schema for the News Fetcher tool."""
        ticker: str = _PydanticField(..., description="Stock ticker symbol (e.g. AAPL, TSLA)")
        max_articles: int = _PydanticField(
            default=20,
            description="Maximum number of articles to return (default 20)"
        )

except ImportError:
    CREWAI_AVAILABLE = False

    class _CrewAIBaseTool:  # type: ignore[no-redef]
        name: str = ""
        description: str = ""

        def _run(self, *args, **kwargs):
            raise NotImplementedError

    NewsFetcherInput = None  # type: ignore[assignment,misc]


# ------------------------------------------------------------------
# Lazy monitor singleton
# ------------------------------------------------------------------
_monitor_cache = None


def _get_monitor():
    """Return a cached EnhancedStockNewsMonitor instance (lightweight, no run loop)."""
    global _monitor_cache
    if _monitor_cache is not None:
        return _monitor_cache

    try:
        from backend.core.stock_monitor import EnhancedStockNewsMonitor
        _monitor_cache = EnhancedStockNewsMonitor()
        return _monitor_cache
    except ImportError:
        pass

    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        from backend.core.stock_monitor import EnhancedStockNewsMonitor
        _monitor_cache = EnhancedStockNewsMonitor()
        return _monitor_cache
    except Exception as e:
        logger.error(f"Failed to create news monitor: {e}")
    return None


# ------------------------------------------------------------------
# The Tool
# ------------------------------------------------------------------
class NewsFetcher(_CrewAIBaseTool):
    """CrewAI-compatible tool that fetches and scores stock news from
    multiple free sources (Google News, Yahoo Finance, Seeking Alpha,
    MarketWatch, Benzinga, Finviz, StockTwits)."""

    name: str = "News Fetcher"
    description: str = (
        "Fetches the latest news articles for a given stock ticker from multiple sources "
        "(Google News, Yahoo Finance, Seeking Alpha, MarketWatch, Benzinga, Finviz, StockTwits). "
        "Returns articles with title, source, URL, and sentiment score/label. "
        "Provide a ticker symbol and optionally max_articles."
    )

    if CREWAI_AVAILABLE and NewsFetcherInput is not None:
        args_schema: Type = NewsFetcherInput  # type: ignore[assignment]

    def _run(self, ticker: str, max_articles: int = 20, **kwargs) -> str:
        """Execute the tool -- called by CrewAI or directly."""
        ticker = ticker.strip().upper()
        return self._fetch_news(ticker, max_articles)

    # ---- public helpers (usable outside CrewAI) -----------------------

    def fetch_news_for_ticker(self, ticker: str, max_articles: int = 20) -> Dict[str, Any]:
        """Return a dict with news articles and sentiment summary."""
        return json.loads(self._fetch_news(ticker.strip().upper(), max_articles))

    # ---- internals ----------------------------------------------------

    def _fetch_news(self, ticker: str, max_articles: int) -> str:
        monitor = _get_monitor()
        if monitor is None:
            return json.dumps({"error": "News monitor not available"})

        all_articles: List[Dict[str, Any]] = []

        # Define fetcher list -- each returns List[Dict]
        fetchers = [
            ("Google News", monitor.fetch_google_news),
            ("Yahoo Finance", monitor.fetch_yahoo_finance_rss),
            ("Seeking Alpha", monitor.fetch_seeking_alpha),
            ("MarketWatch", monitor.fetch_marketwatch),
            ("Benzinga", monitor.fetch_benzinga),
            ("Finviz", monitor.fetch_finviz_news),
            ("StockTwits", monitor.fetch_stocktwits),
        ]

        # Add India-specific fetchers for Indian tickers
        is_indian = '.NS' in ticker.upper() or '.BO' in ticker.upper()
        if is_indian:
            fetchers.extend([
                ("Economic Times", monitor.fetch_economic_times),
                ("Moneycontrol", monitor.fetch_moneycontrol),
                ("Mint", monitor.fetch_mint),
            ])

        source_counts: Dict[str, int] = {}

        for source_name, fetcher in fetchers:
            try:
                articles = fetcher(ticker)
                for article in articles:
                    # Compute sentiment using the monitor's method
                    full_text = f"{article.get('title', '')} {article.get('description', '')}"
                    score, label = monitor.calculate_sentiment(
                        full_text, article.get('engagement_score', 0)
                    )

                    all_articles.append({
                        "title": article.get('title', ''),
                        "description": (article.get('description', '') or '')[:300],
                        "url": article.get('url', ''),
                        "source": source_name,
                        "published_date": article.get('published_date', ''),
                        "engagement_score": article.get('engagement_score', 0),
                        "sentiment_score": round(score, 3),
                        "sentiment_label": label,
                    })
                    source_counts[source_name] = source_counts.get(source_name, 0) + 1
            except Exception as e:
                logger.warning(f"News fetcher {source_name} failed for {ticker}: {e}")

        # Sort by engagement score descending, then trim
        all_articles.sort(key=lambda a: a['engagement_score'], reverse=True)
        all_articles = all_articles[:max_articles]

        # Compute aggregate sentiment
        if all_articles:
            scores = [a['sentiment_score'] for a in all_articles]
            avg_sentiment = sum(scores) / len(scores)
            positive_count = sum(1 for a in all_articles if a['sentiment_label'] == 'positive')
            negative_count = sum(1 for a in all_articles if a['sentiment_label'] == 'negative')
            neutral_count = sum(1 for a in all_articles if a['sentiment_label'] == 'neutral')
        else:
            avg_sentiment = 0.0
            positive_count = negative_count = neutral_count = 0

        return json.dumps({
            "ticker": ticker,
            "total_articles": len(all_articles),
            "sources_used": source_counts,
            "avg_sentiment": round(avg_sentiment, 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "articles": all_articles,
            "fetched_at": datetime.utcnow().isoformat(),
        })
