```python
"""
Metrics Extractor - Extract key metrics from stocks, ratings, and news tables.

This module provides utilities to extract market data for research briefs:
- Current price and price change
- RSI and technical indicators
- Sentiment scores from news
- Count of recent news articles
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal

from backend.config import Config
from backend.database import db_session

logger = logging.getLogger(__name__)


class MetricsExtractor:
    """Extract key metrics for a given ticker from related tables."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        self.db_path = db_path or Config.DB_PATH

    def extract_brief_metrics(self, ticker: str) -> Dict[str, Any]:
        """
        Extract all key metrics for a brief.

        Returns dict with:
        - current_price (float)
        - price_change_24h_pct (float)
        - rsi (float)
        - sentiment_score (float)
        - sentiment_label (str)
        - news_count_7d (int)
        - metric_sources (list): ["stocks", "ai_ratings", "news"]
        """
        metrics = {}
        sources = []

        try:
            with db_session(self.db_path) as conn:
                # Extract price data from stocks table
                price_data = self._get_price_data(conn, ticker)
                if price_data:
                    metrics.update(price_data)
                    sources.append("stocks")

                # Extract technical metrics from ai_ratings
                technical_data = self._get_technical_data(conn, ticker)
                if technical_data:
                    metrics.update(technical_data)
                    sources.append("ai_ratings")

                # Extract sentiment from news
                sentiment_data = self._get_sentiment_data(conn, ticker)
                if sentiment_data:
                    metrics.update(sentiment_data)
                    sources.append("news")

            metrics["metric_sources"] = sources
            return metrics

        except Exception as e:
            logger.error(f"Error extracting metrics for {ticker}: {e}")
            return {"metric_sources": []}

    def _get_price_data(self, conn: sqlite3.Connection, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current price and price change from stocks table."""
        try:
            row = conn.execute(
                "SELECT current_price, price_change_pct FROM stocks WHERE ticker = ?",
                (ticker,)
            ).fetchone()

            if row:
                return {
                    "current_price": float(row[0]) if row[0] else None,
                    "price_change_24h_pct": float(row[1]) if row[1] else None,
                }
        except Exception as e:
            logger.warning(f"Error getting price data for {ticker}: {e}")

        return None

    def _get_technical_data(self, conn: sqlite3.Connection, ticker: str) -> Optional[Dict[str, Any]]:
        """Get RSI and sentiment from ai_ratings table."""
        try:
            row = conn.execute(
                """SELECT rsi, sentiment_score, sentiment_label, technical_score, fundamental_score
                   FROM ai_ratings WHERE ticker = ? ORDER BY updated_at DESC LIMIT 1""",
                (ticker,)
            ).fetchone()

            if row:
                return {
                    "rsi": float(row[0]) if row[0] else None,
                    "sentiment_score": float(row[1]) if row[1] else None,
                    "sentiment_label": row[2] if row[2] else None,
                    "technical_score": float(row[3]) if row[3] else None,
                    "fundamental_score": float(row[4]) if row[4] else None,
                }
        except Exception as e:
            logger.warning(f"Error getting technical data for {ticker}: {e}")

        return None

    def _get_sentiment_data(self, conn: sqlite3.Connection, ticker: str) -> Optional[Dict[str, Any]]:
        """Get sentiment and news count from news table (last 7 days)."""
        try:
            seven_days_ago = datetime.now() - timedelta(days=7)

            # Get recent news count
            count_row = conn.execute(
                """SELECT COUNT(*) as cnt FROM news
                   WHERE ticker = ? AND created_at >= ?""",
                (ticker, seven_days_ago)
            ).fetchone()

            news_count_7d = count_row[0] if count_row else 0

            # Get average sentiment from recent news
            sentiment_row = conn.execute(
                """SELECT AVG(
                    CASE
                        WHEN sentiment_label = 'bullish' THEN 1.0
                        WHEN sentiment_label = 'neutral' THEN 0.5
                        WHEN sentiment_label = 'bearish' THEN 0.0
                        ELSE 0.5
                    END
                ) as avg_sentiment
                FROM news WHERE ticker = ? AND created_at >= ?""",
                (ticker, seven_days_ago)
            ).fetchone()

            avg_sentiment = sentiment_row[0] if sentiment_row and sentiment_row[0] else None

            return {
                "news_count_7d": news_count_7d,
                "recent_sentiment_avg": avg_sentiment,
            }
        except Exception as e:
            logger.warning(f"Error getting sentiment data for {ticker}: {e}")

        return None

    def extract_key_insights(self, ticker: str, content: str, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate 3-5 key insights from brief content and metrics.

        Returns list of insight strings.
        """
        insights = []

        try:
            # Extract insights from content and metrics
            if metrics.get("sentiment_label"):
                sentiment = metrics.get("sentiment_label", "").lower()
                if sentiment == "bullish":
                    insights.append(f"Market sentiment for {ticker} is bullish based on recent analysis")
                elif sentiment == "bearish":
                    insights.append(f"Market sentiment for {ticker} is bearish - proceed with caution")

            if metrics.get("rsi"):
                rsi = metrics.get("rsi", 0)
                if rsi > 70:
                    insights.append(f"RSI at {rsi:.1f} indicates overbought conditions")
                elif rsi < 30:
                    insights.append(f"RSI at {rsi:.1f} indicates oversold conditions")

            if metrics.get("price_change_24h_pct"):
                change = metrics.get("price_change_24h_pct", 0)
                if abs(change) > 2:
                    insights.append(f"Significant 24h price movement of {change:+.2f}%")

            if metrics.get("news_count_7d"):
                news_count = metrics.get("news_count_7d", 0)
                if news_count > 5:
                    insights.append(f"High news activity with {news_count} articles in last 7 days")

            # Extract first sentence if available
            if content:
                first_sentence = content.split('.')[0] + '.' if content else ""
                if len(first_sentence) > 20 and len(insights) < 5:
                    # Extract a meaningful summary
                    if "support" in content.lower() or "resistance" in content.lower():
                        insights.append("Key technical support and resistance levels identified")

        except Exception as e:
            logger.warning(f"Error generating insights for {ticker}: {e}")

        # Return up to 5 insights
        return insights[:5]

    def extract_summary(self, brief_content: str, max_chars: int = 250) -> str:
        """
        Extract or generate executive summary from brief content.

        Truncates first paragraph or uses first 250 characters.
        """
        try:
            # Split by double newline or period
            paragraphs = brief_content.split('\n\n')
            if paragraphs and paragraphs[0]:
                summary = paragraphs[0].strip()
                if len(summary) > max_chars:
                    # Truncate at word boundary
                    truncated = summary[:max_chars]
                    last_space = truncated.rfind(' ')
                    if last_space > 0:
                        return truncated[:last_space] + "..."
                    return truncated + "..."
                return summary
            return brief_content[:max_chars] + "..." if len(brief_content) > max_chars else brief_content
        except Exception as e:
            logger.warning(f"Error extracting summary: {e}")
            return brief_content[:max_chars]


def extract_metrics_for_brief(ticker: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to extract metrics for a brief."""
    extractor = MetricsExtractor(db_path)
    return extractor.extract_brief_metrics(ticker)
```