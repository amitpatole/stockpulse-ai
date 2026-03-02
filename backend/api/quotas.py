```python
"""
TickerPulse AI v3.0 - API Quotas Endpoint
Provides real-time API usage and rate limit information across all providers.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from backend.core.quota_manager import get_quota_manager

logger = logging.getLogger(__name__)

quotas_bp = Blueprint('quotas', __name__, url_prefix='/api')


@quotas_bp.route('/quotas', methods=['GET'])
def get_quotas():
    """
    Get all API quotas and current usage across all providers.

    Returns
    -------
    dict
        List of quota objects with usage metrics and status indicators
    int
        HTTP status code (200 on success)

    Response Example
    ----------------
    {
        "data": [
            {
                "provider": "sec",
                "quota_type": "bulk_submissions",
                "limit": 100,
                "used": 42,
                "percent_used": 42,
                "reset_at": "2026-03-03T00:00:00Z",
                "status": "normal"
            },
            {
                "provider": "tradingview",
                "quota_type": "api_calls",
                "limit": 500,
                "used": 450,
                "percent_used": 90,
                "reset_at": "2026-03-02T15:00:00Z",
                "status": "critical"
            }
        ],
        "meta": {
            "updated_at": "2026-03-02T10:30:00Z",
            "total_providers": 2
        }
    }
    """
    try:
        quota_manager = get_quota_manager()
        quotas = quota_manager.get_all_quotas()

        return jsonify({
            'data': quotas,
            'meta': {
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'total_providers': len(set(q['provider'] for q in quotas)),
            },
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving quotas: {e}")
        return jsonify({
            'error': 'Failed to retrieve quotas',
            'details': str(e),
        }), 500


@quotas_bp.route('/quotas/<provider_name>', methods=['GET'])
def get_provider_quotas(provider_name: str):
    """
    Get API quotas for a specific provider.

    Parameters
    ----------
    provider_name : str
        Name of the provider (e.g., 'sec', 'tradingview', 'coingecko')

    Returns
    -------
    dict
        List of quota objects for the specified provider
    int
        HTTP status code (200 on success)
    """
    try:
        quota_manager = get_quota_manager()
        quotas = quota_manager.get_provider_quotas(provider_name)

        if not quotas:
            return jsonify({
                'data': [],
                'meta': {
                    'provider': provider_name,
                    'updated_at': datetime.utcnow().isoformat() + 'Z',
                },
            }), 200

        return jsonify({
            'data': quotas,
            'meta': {
                'provider': provider_name,
                'updated_at': datetime.utcnow().isoformat() + 'Z',
            },
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving quotas for {provider_name}: {e}")
        return jsonify({
            'error': 'Failed to retrieve quotas',
            'details': str(e),
        }), 500


@quotas_bp.route('/quotas/history', methods=['GET'])
def get_quota_history():
    """
    Get historical quota data for the last 48 hours or specified time period.

    Query Parameters
    ----------------
    provider : str, optional
        Filter by specific provider name
    hours : int, optional
        Number of hours of history to retrieve (default: 48)
    limit : int, optional
        Maximum records to return (default: 100, max: 100)

    Returns
    -------
    dict
        List of historical quota records
    int
        HTTP status code (200 on success)

    Response Example
    ----------------
    {
        "data": [
            {
                "provider": "sec",
                "quota_type": "bulk",
                "used": 42,
                "limit": 100,
                "percent_used": 42,
                "recorded_at": "2026-03-02T10:30:00Z"
            }
        ],
        "meta": {
            "time_range": "48h",
            "intervals": 96,
            "provider": "sec"
        }
    }
    """
    try:
        quota_manager = get_quota_manager()

        # Get query parameters
        provider_name = request.args.get('provider', None)
        hours = request.args.get('hours', 48, type=int)
        limit = request.args.get('limit', 100, type=int)

        # Clamp hours and limit
        hours = max(1, min(hours, 720))  # 1 hour to 30 days
        limit = max(1, min(limit, 100))

        history = quota_manager.get_quota_history(
            provider_name=provider_name,
            hours=hours,
            limit=limit
        )

        return jsonify({
            'data': history,
            'meta': {
                'time_range': f'{hours}h',
                'records': len(history),
                'provider': provider_name or 'all',
            },
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving quota history: {e}")
        return jsonify({
            'error': 'Failed to retrieve quota history',
            'details': str(e),
        }), 500


@quotas_bp.route('/quotas/<provider_name>/analytics', methods=['GET'])
def get_provider_analytics(provider_name: str):
    """
    Get provider-specific quota analytics and trends.

    Parameters
    ----------
    provider_name : str
        Name of the provider

    Query Parameters
    ----------------
    hours : int, optional
        Number of hours to analyze (default: 48)

    Returns
    -------
    dict
        Analytics including peak usage, average usage, quota types
    int
        HTTP status code (200 on success)

    Response Example
    ----------------
    {
        "data": {
            "provider": "sec",
            "peak_usage_percent": 95,
            "average_usage_percent": 65,
            "quota_types": ["bulk_submissions", "daily_requests"],
            "hours_analyzed": 48,
            "total_records": 96
        },
        "meta": {
            "provider": "sec",
            "analyzed_at": "2026-03-02T10:30:00Z"
        }
    }
    """
    try:
        quota_manager = get_quota_manager()
        hours = request.args.get('hours', 48, type=int)

        # Clamp hours
        hours = max(1, min(hours, 720))

        analytics = quota_manager.get_provider_analytics(provider_name, hours=hours)

        return jsonify({
            'data': analytics,
            'meta': {
                'provider': provider_name,
                'analyzed_at': datetime.utcnow().isoformat() + 'Z',
            },
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving provider analytics for {provider_name}: {e}")
        return jsonify({
            'error': 'Failed to retrieve provider analytics',
            'details': str(e),
        }), 500
```