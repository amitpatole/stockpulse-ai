```python
"""
TickerPulse AI v3.0 - Research API Routes
Blueprint for AI-generated research briefs.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import sqlite3
import random
import logging
from typing import Dict

from backend.config import Config
from backend.core.query_optimizer import get_research_briefs_by_ticker

logger = logging.getLogger(__name__)

research_bp = Blueprint('research', __name__, url_prefix='/api')


@research_bp.route('/research/briefs', methods=['GET'])
def list_briefs():
    """List paginated research briefs with optimized single-query pagination.

    Query Parameters:
        ticker (str, optional): Filter by stock ticker.
        limit (int, optional): Max briefs to return. Default: 25, Max: 100.
        offset (int, optional): Number of records to skip. Default: 0.

    Returns:
        JSON object with 'data' array of briefs and 'meta' containing pagination info.
    """
    ticker = request.args.get('ticker', None)

    # Validate and parse pagination parameters
    try:
        limit = min(int(request.args.get('limit', 25)), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
    except (ValueError, TypeError):
        limit = 25
        offset = 0

    try:
        # OPTIMIZATION: Use optimized single-query pagination (combines COUNT + SELECT into one query)
        if ticker:
            briefs_list, total_count = get_research_briefs_by_ticker(ticker, limit=limit, offset=offset)
        else:
            # For all briefs, fetch all and paginate in Python
            # (TODO: Could optimize to fetch limit+1 and detect has_next without separate COUNT)
            conn = sqlite3.connect(Config.DB_PATH)
            conn.row_factory = sqlite3.Row

            count_row = conn.execute(
                'SELECT COUNT(*) as count FROM research_briefs'
            ).fetchone()
            total_count = count_row['count'] if count_row else 0

            rows = conn.execute(
                'SELECT id, ticker, title, content, agent_name, model_used, created_at FROM research_briefs ORDER BY created_at DESC LIMIT ? OFFSET ?',
                (limit, offset)
            ).fetchall()
            conn.close()

            briefs_list = [dict(row) for row in rows]

        briefs = [{
            'id': b['id'],
            'ticker': b['ticker'],
            'title': b['title'],
            'content': b['content'],
            'agent_name': b['agent_name'],
            'model_used': b['model_used'],
            'created_at': b['created_at'],
        } for b in briefs_list]

        # Calculate pagination info
        has_next = (offset + limit) < total_count
        has_previous = offset > 0

        meta = {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': has_next,
            'has_previous': has_previous,
        }

        return jsonify({'data': briefs, 'meta': meta})
    except Exception as e:
        logger.error(f"Error fetching research briefs: {e}")
        return jsonify({'data': [], 'meta': {'total': 0, 'limit': limit, 'offset': offset, 'has_next': False, 'has_previous': False}}), 500


@research_bp.route('/research/briefs', methods=['POST'])
def generate_brief():
    """Trigger generation of a new research brief.

    Request Body (JSON, optional):
        ticker (str): Stock ticker to research. If omitted, picks from watchlist.

    Returns:
        JSON object with the generated brief.
    """
    data = request.get_json(silent=True) or {}
    ticker = data.get('ticker', '').upper()

    if not ticker:
        # Pick a random ticker from the watchlist
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT ticker FROM stocks WHERE active = 1').fetchall()
            conn.close()
            if rows:
                ticker = random.choice(rows)['ticker']
            else:
                ticker = 'AAPL'
        except Exception:
            ticker = 'AAPL'

    brief = _generate_sample_brief(ticker)
    return jsonify(brief)


def _generate_sample_brief(ticker: str) -> Dict:
    """Generate and store a sample research brief for a given ticker."""

    # Get current price and rating data if available
    price_info = ''
    rating_info = ''
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        stock = conn.execute(
            'SELECT current_price, price_change_pct FROM stocks WHERE ticker = ?',
            (ticker,)
        ).fetchone()
        if stock and stock['current_price']:
            price_info = f"Currently trading at ${stock['current_price']:.2f} ({stock['price_change_pct']:+.2f}%)"

        rating = conn.execute(
            'SELECT rating, score, rsi, sentiment_score, sentiment_label, technical_score, fundamental_score FROM ai_ratings WHERE ticker = ?',
            (ticker,)
        ).fetchone()
        if rating:
            rating_info = f"AI Rating: {rating['rating']} (Score: {rating['score']}/10)"

        conn.close()
    except Exception:
        pass

    templates = [
        {
            'title': f'{ticker} Deep Dive: Technical & Fundamental Analysis',
            'content': f"""## Executive Summary

{ticker} presents an interesting setup for investors. {price_info}. {rating_info}.

## Technical Analysis

The stock's RSI is currently in a neutral zone, suggesting neither overbought nor oversold conditions. Key moving averages remain supportive of the current trend.

**Key Levels:**
- Support: Recent consolidation zone provides strong support
- Resistance: Previous highs form a key resistance area
- Volume: Trading volume has been consistent with the 20-day average

## Fundamental Overview

The company continues to demonstrate solid fundamentals:
- Revenue growth trajectory remains intact
- Margins are stable or expanding
- Balance sheet strength provides a buffer against market volatility

## Sentiment Analysis

Market sentiment for {ticker} is currently leaning positive based on:
- News flow has been constructive
- Social media mentions show growing interest
- Institutional positioning appears favorable

## Risk Factors

- Broader market volatility could impact near-term performance
- Sector rotation could create headwinds
- Macroeconomic uncertainty remains elevated

## Conclusion

{ticker} warrants continued monitoring. The technical setup combined with solid fundamentals suggests a constructive outlook, though investors should remain mindful of broader market risks.""",
        },
        {
            'title': f'{ticker} Research Brief: Market Position & Outlook',
            'content': f"""## Overview

This research brief examines {ticker}'s current market position and near-term outlook. {price_info}. {rating_info}.

## Market Context

The broader market environment continues to be shaped by:
- Federal Reserve monetary policy expectations
- Earnings season dynamics
- Geopolitical considerations

## Company Analysis

### Strengths
- Strong competitive moat in core business segments
- Consistent execution on strategic initiatives
- Robust cash flow generation

### Catalysts
- Upcoming product launches or earnings reports
- Industry tailwinds in key growth segments
- Potential for margin expansion

## Technical Picture

The chart pattern suggests the stock is in a consolidation phase after recent moves. Key technical indicators:
- RSI: Moderate levels suggest room for movement in either direction
- MACD: Signal line positioning will be crucial for near-term direction
- Moving Averages: Price relationship with key MAs remains constructive

## Social Sentiment

Reddit and social media analysis indicates:
- Moderate but growing retail interest
- Discussion sentiment is predominantly constructive
- No unusual options activity flagged

## Investment Thesis

{ticker} offers a balanced risk-reward profile at current levels. The combination of solid fundamentals, constructive technicals, and positive sentiment provides a supportive backdrop for the stock.""",
        },
    ]

    template = random.choice(templates)
    now = datetime.now(timezone.utc).isoformat()

    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.execute(
            """INSERT INTO research_briefs
               (ticker, title, content, agent_name, model_used, created_at)
               VALUES (?, ?, ?, 'researcher', 'claude-sonnet-4-5 (stub)', ?)""",
            (ticker, template['title'], template['content'], now)
        )
        brief_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            'id': brief_id,
            'ticker': ticker,
            'title': template['title'],
            'content': template['content'],
            'agent_name': 'researcher',
            'model_used': 'claude-sonnet-4-5 (stub)',
            'created_at': now,
        }
    except Exception as e:
        logger.error(f"Error saving research brief: {e}")
        return {
            'id': 0,
            'ticker': ticker,
            'title': template['title'],
            'content': template['content'],
            'agent_name': 'researcher',
            'model_used': 'claude-sonnet-4-5 (stub)',
            'created_at': now,
        }
```