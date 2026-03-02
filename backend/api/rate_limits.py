```python
"""
TickerPulse AI v3.0 - Rate Limits API
Endpoints for retrieving API usage and rate limit metrics.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from backend.core.rate_limit_manager import RateLimitManager

logger = logging.getLogger(__name__)

bp = Blueprint('rate_limits', __name__, url_prefix='/api/rate-limits')


@bp.route('', methods=['GET'])
def get_all_rate_limits():
    """
    Get current usage and status for all API providers.
    
    Returns
    -------
    dict with keys:
        - data: List of provider usage objects
        - meta: Metadata (total_providers, timestamp)
        - errors: List of errors (empty if successful)
    """
    try:
        providers = RateLimitManager.get_all_providers()
        
        return jsonify({
            'data': providers,
            'meta': {
                'total_providers': len(providers),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            },
            'errors': []
        }), 200
    except Exception as e:
        logger.error(f"Failed to get rate limits: {e}", exc_info=True)
        return jsonify({
            'data': [],
            'meta': {
                'total_providers': 0,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            },
            'errors': ['Failed to retrieve rate limits']
        }), 500


@bp.route('/<provider>/history', methods=['GET'])
def get_provider_history(provider):
    """
    Get historical usage data for a specific provider.
    
    Query Parameters
    ----------------
    hours : int
        Number of hours to retrieve (1-720, default 24)
    interval : str
        Aggregation interval (hourly or daily, default hourly)
    
    Returns
    -------
    dict with keys:
        - data: List of hourly/daily usage records
        - meta: Metadata (provider, oldest/newest timestamps, totals)
        - errors: List of errors
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        interval = request.args.get('interval', 'hourly', type=str)
        
        # Validate hours
        if not (1 <= hours <= 720):
            return jsonify({
                'data': [],
                'meta': {},
                'errors': ['Invalid hours: must be between 1 and 720']
            }), 400
        
        # Validate interval
        if interval not in ('hourly', 'daily'):
            return jsonify({
                'data': [],
                'meta': {},
                'errors': ['Invalid interval: must be hourly or daily']
            }), 400
        
        history = RateLimitManager.get_usage_history(
            provider_name=provider,
            hours=hours,
            interval=interval
        )
        
        if not history:
            return jsonify({
                'data': [],
                'meta': {
                    'provider': provider,
                    'oldest_timestamp': None,
                    'newest_timestamp': None,
                    'total_calls': 0,
                    'total_errors': 0
                },
                'errors': []
            }), 200
        
        total_calls = sum(h['call_count'] for h in history)
        total_errors = sum(h['errors'] for h in history)
        
        return jsonify({
            'data': history,
            'meta': {
                'provider': provider,
                'oldest_timestamp': history[0]['timestamp'],
                'newest_timestamp': history[-1]['timestamp'],
                'total_calls': total_calls,
                'total_errors': total_errors
            },
            'errors': []
        }), 200
    except Exception as e:
        logger.error(f"Failed to get history for {provider}: {e}", exc_info=True)
        return jsonify({
            'data': [],
            'meta': {},
            'errors': ['Failed to retrieve usage history']
        }), 500
```