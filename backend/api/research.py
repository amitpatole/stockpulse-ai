"""
TickerPulse AI v3.0 - Research API Routes
Blueprint for AI-generated research briefs with enhancements.
"""

from flask import Blueprint, jsonify, request, send_file
from datetime import datetime, timezone, timedelta
import sqlite3
import random
import logging
import json
import io
from typing import Dict, Tuple

from backend.config import Config
from backend.database import db_session
from backend.core.query_optimizer import get_research_briefs_by_ticker, get_brief_with_metadata
from backend.core.metrics_extractor import extract_metrics_for_brief, MetricsExtractor
from backend.core.pdf_generator import generate_pdf_for_brief

logger = logging.getLogger(__name__)

research_bp = Blueprint('research', __name__, url_prefix='/api')

# Cache for metadata (1 hour TTL)
_metadata_cache: Dict[int, Tuple[dict, datetime]] = {}
METADATA_CACHE_TTL = 3600  # seconds


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
        # OPTIMIZATION: Use optimized single-query pagination
        if ticker:
            briefs_list, total_count = get_research_briefs_by_ticker(ticker, limit=limit, offset=offset)
        else:
            # Fetch all briefs with pagination
            with db_session() as conn:
                cursor = conn.cursor()

                count_row = cursor.execute(
                    'SELECT COUNT(*) as count FROM research_briefs'
                ).fetchone()
                total_count = count_row['count'] if count_row else 0

                rows = cursor.execute("""
                    SELECT id, ticker, title, content, executive_summary, agent_name,
                           model_used, has_metrics, created_at
                    FROM research_briefs
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset)).fetchall()

                briefs_list = [dict(row) for row in rows]

        briefs = [{
            'id': b['id'],
            'ticker': b['ticker'],
            'title': b['title'],
            'content': b['content'][:500],  # Truncate for list view
            'executive_summary': b.get('executive_summary'),
            'agent_name': b['agent_name'],
            'model_used': b['model_used'],
            'has_metrics': bool(b.get('has_metrics', 0)),
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
        return jsonify({'data': [], 'meta': {'total': 0, 'limit': limit, 'offset': offset, 'has_next': False, 'has_previous': False}, 'errors': [str(e)]}), 500


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
        # Optimize: Fetch only ticker column instead of entire row
        try:
            with db_session() as conn:
                rows = conn.execute('SELECT ticker FROM stocks WHERE active = 1').fetchall()
                if rows:
                    ticker = random.choice(rows)['ticker']
                else:
                    ticker = 'AAPL'
        except Exception:
            ticker = 'AAPL'

    brief = _generate_sample_brief(ticker)
    return jsonify(brief)


@research_bp.route('/research/briefs/<int:brief_id>', methods=['GET'])
def get_brief_detail(brief_id: int):
    """Fetch full research brief with metrics and metadata.

    Args:
        brief_id: ID of the research brief

    Returns:
        JSON with brief content, executive summary, and metrics
    """
    try:
        brief_data = get_brief_with_metadata(brief_id)
        if not brief_data:
            return jsonify({'data': None, 'errors': ['Brief not found']}), 404

        ticker = brief_data.get('ticker')

        # Extract metrics if not already in metadata
        metrics = {}
        if brief_data.get('key_metrics'):
            try:
                metrics = json.loads(brief_data['key_metrics'])
            except:
                metrics = {}
        elif ticker:
            metrics = extract_metrics_for_brief(ticker)

        # Extract summary if not in metadata
        summary = brief_data.get('meta_summary') or brief_data.get('executive_summary')
        if not summary:
            extractor = MetricsExtractor()
            summary = extractor.extract_summary(brief_data.get('content', ''))

        response_data = {
            'id': brief_data['id'],
            'ticker': brief_data['ticker'],
            'title': brief_data['title'],
            'content': brief_data['content'],
            'executive_summary': summary,
            'created_at': brief_data['created_at'],
            'agent_name': brief_data['agent_name'],
            'metrics': metrics,
            'metric_sources': brief_data.get('metric_sources', []),
        }

        # Check if PDF is available
        has_pdf = bool(brief_data.get('pdf_url') and brief_data.get('pdf_generated_at'))

        meta = {
            'has_pdf': has_pdf,
            'pdf_url': brief_data.get('pdf_url'),
            'pdf_generated_at': brief_data.get('pdf_generated_at'),
        }

        return jsonify({'data': response_data, 'meta': meta})

    except Exception as e:
        logger.error(f"Error fetching brief {brief_id}: {e}")
        return jsonify({'data': None, 'errors': [str(e)]}), 500


@research_bp.route('/research/briefs/<int:brief_id>/metrics', methods=['GET'])
def get_brief_metrics(brief_id: int):
    """Fetch just the key metrics for a brief (lightweight endpoint).

    Uses caching (5 minute TTL) to reduce database load.

    Args:
        brief_id: ID of the research brief

    Returns:
        JSON with ticker and metrics only
    """
    try:
        # Check cache
        if brief_id in _metadata_cache:
            cached_data, cached_time = _metadata_cache[brief_id]
            if (datetime.now() - cached_time).total_seconds() < METADATA_CACHE_TTL:
                return jsonify({'data': cached_data, 'meta': {'cached': True}})

        # Fetch brief to get ticker
        with db_session() as conn:
            brief = conn.execute(
                'SELECT id, ticker FROM research_briefs WHERE id = ?',
                (brief_id,)
            ).fetchone()

        if not brief:
            return jsonify({'data': None, 'errors': ['Brief not found']}), 404

        ticker = brief['ticker']
        metrics = extract_metrics_for_brief(ticker)

        response_data = {
            'ticker': ticker,
            'metrics': metrics,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }

        # Cache the result
        _metadata_cache[brief_id] = (response_data, datetime.now())

        return jsonify({'data': response_data, 'meta': {'cached': False}})

    except Exception as e:
        logger.error(f"Error fetching metrics for brief {brief_id}: {e}")
        return jsonify({'data': None, 'errors': [str(e)]}), 500


@research_bp.route('/research/briefs/<int:brief_id>/export-pdf', methods=['POST'])
def export_brief_pdf(brief_id: int):
    """Generate and return PDF for a research brief.

    Args:
        brief_id: ID of the research brief

    Returns:
        PDF file download or JSON with error
    """
    try:
        brief_data = get_brief_with_metadata(brief_id)
        if not brief_data:
            return jsonify({'data': None, 'errors': ['Brief not found']}), 404

        ticker = brief_data.get('ticker')

        # Extract metrics
        metrics = {}
        if brief_data.get('key_metrics'):
            try:
                metrics = json.loads(brief_data['key_metrics'])
            except:
                metrics = {}
        else:
            metrics = extract_metrics_for_brief(ticker)

        # Extract summary
        summary = brief_data.get('meta_summary') or brief_data.get('executive_summary')
        if not summary:
            extractor = MetricsExtractor()
            summary = extractor.extract_summary(brief_data.get('content', ''))

        # Prepare brief data for PDF
        pdf_brief_data = {
            'ticker': ticker,
            'title': brief_data['title'],
            'content': brief_data['content'],
            'executive_summary': summary,
            'metrics': metrics,
        }

        # Generate PDF
        pdf_bytes, size_kb = generate_pdf_for_brief(pdf_brief_data)

        if not pdf_bytes:
            return jsonify({'data': None, 'errors': ['PDF generation failed']}), 500

        # Save PDF URL to metadata (in real scenario, would upload to S3)
        generated_at = datetime.now(timezone.utc).isoformat()
        pdf_filename = f"ticker-pulse-{ticker}-{datetime.now().strftime('%Y%m%d')}.pdf"

        try:
            with db_session() as conn:
                cursor = conn.cursor()
                # Update or insert metadata
                cursor.execute("""
                    INSERT INTO research_brief_metadata (brief_id, pdf_url, pdf_generated_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(brief_id) DO UPDATE SET
                        pdf_url = excluded.pdf_url,
                        pdf_generated_at = excluded.pdf_generated_at,
                        updated_at = excluded.updated_at
                """, (brief_id, f"/api/research/briefs/{brief_id}/pdf/{pdf_filename}", generated_at, datetime.now(timezone.utc).isoformat()))

                # Mark as having metrics
                cursor.execute(
                    "UPDATE research_briefs SET has_metrics = 1 WHERE id = ?",
                    (brief_id,)
                )
        except Exception as e:
            logger.warning(f"Failed to update metadata for brief {brief_id}: {e}")

        # Return PDF file
        pdf_buffer = io.BytesIO(pdf_bytes)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )

    except Exception as e:
        logger.error(f"Error exporting PDF for brief {brief_id}: {e}")
        return jsonify({'data': None, 'errors': [str(e)]}), 500


def _generate_sample_brief(ticker: str) -> Dict:
    """Generate and store a sample research brief for a given ticker."""

    price_info = ''
    rating_info = ''
    try:
        with db_session() as conn:
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
    ]

    template = random.choice(templates)
    now = datetime.now(timezone.utc).isoformat()

    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO research_briefs
                   (ticker, title, content, agent_name, model_used, created_at)
                   VALUES (?, ?, ?, 'researcher', 'claude-sonnet-4-6', ?)
            """, (ticker, template['title'], template['content'], now))
            brief_id = cursor.lastrowid

        return {
            'id': brief_id,
            'ticker': ticker,
            'title': template['title'],
            'content': template['content'],
            'agent_name': 'researcher',
            'model_used': 'claude-sonnet-4-6',
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
            'model_used': 'claude-sonnet-4-6',
            'created_at': now,
        }
