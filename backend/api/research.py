"""
TickerPulse AI v3.0 - Research API Routes
Blueprint for AI-generated research briefs.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import sqlite3
import random
import logging

from backend.config import Config

logger = logging.getLogger(__name__)

research_bp = Blueprint('research', __name__, url_prefix='/api')


def _parse_pagination(args):
    """Parse and validate page/page_size query parameters.

    Supports the legacy ``limit`` parameter (treated as ``page_size``).
    Returns (page, page_size, error_response). On success, error_response is None.
    On validation failure, page and page_size are None and error_response is a
    (response, status_code) tuple ready to return from a Flask view.
    """
    try:
        page = int(args.get('page', 1))
        if 'limit' in args and 'page_size' not in args:
            logger.warning(
                "Query param 'limit' is deprecated for /api/research/briefs; "
                "use 'page_size' instead."
            )
            page_size = int(args.get('limit'))
        else:
            page_size = int(args.get('page_size', 25))
    except (ValueError, TypeError):
        return None, None, (jsonify({'error': 'page and page_size must be integers'}), 400)

    if not (1 <= page_size <= 100):
        return None, None, (jsonify({'error': 'page_size must be between 1 and 100'}), 400)

    return page, page_size, None


@research_bp.route('/research/briefs', methods=['GET'])
def list_briefs():
    """List research briefs, optionally filtered by ticker.

    Query Parameters:
        ticker (str, optional): Filter by stock ticker.
        page (int, optional): Page number, 1-based. Default 1.
        page_size (int, optional): Results per page, 1-100. Default 25.
        limit (int, deprecated): Alias for page_size for backwards compatibility.

    Returns:
        JSON envelope with data array and pagination metadata.
    """
    ticker = request.args.get('ticker', None)
    page, page_size, err = _parse_pagination(request.args)
    if err:
        return err

    offset = (page - 1) * page_size

    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        if ticker:
            total = conn.execute(
                'SELECT COUNT(*) FROM research_briefs WHERE ticker = ?',
                (ticker.upper(),)
            ).fetchone()[0]
            rows = conn.execute(
                'SELECT * FROM research_briefs WHERE ticker = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
                (ticker.upper(), page_size, offset)
            ).fetchall()
        else:
            total = conn.execute(
                'SELECT COUNT(*) FROM research_briefs'
            ).fetchone()[0]
            rows = conn.execute(
                'SELECT * FROM research_briefs ORDER BY created_at DESC LIMIT ? OFFSET ?',
                (page_size, offset)
            ).fetchall()
        conn.close()

        briefs = [{
            'id': r['id'],
            'ticker': r['ticker'],
            'title': r['title'],
            'content': r['content'],
            'agent_name': r['agent_name'],
            'model_used': r['model_used'],
            'created_at': r['created_at'],
        } for r in rows]

        return jsonify({
            'data': briefs,
            'page': page,
            'page_size': page_size,
            'total': total,
            'has_next': (page * page_size) < total,
        })
    except Exception as e:
        logger.error(f"Error fetching research briefs: {e}")
        return jsonify({'data': [], 'page': page, 'page_size': page_size, 'total': 0, 'has_next': False})


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


def _generate_sample_brief(ticker: str) -> dict:
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
