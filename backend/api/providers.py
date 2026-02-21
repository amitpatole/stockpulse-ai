"""
TickerPulse AI v3.0 - Data Provider Status API
Exposes per-provider rate limit counters for the Settings UI.
"""

import logging
from datetime import datetime

from flask import Blueprint, current_app, jsonify

logger = logging.getLogger(__name__)

providers_bp = Blueprint('providers', __name__, url_prefix='/api')


@providers_bp.route('/providers/status', methods=['GET'])
def get_providers_status():
    """Return current rate limit status for all registered data providers.

    Reads live in-memory counters from the ``DataProviderRegistry`` so the
    numbers are always up-to-date without waiting for a scheduled DB flush.

    Returns:
        JSON object::

            {
                "providers": [
                    {
                        "id": "yahoo_finance",
                        "display_name": "Yahoo Finance",
                        "is_active": true,
                        "rate_limit_used": 42,
                        "rate_limit_max": 120,
                        "reset_at": "2026-02-21T14:01:00Z"
                    }
                ]
            }
    """
    registry = current_app.extensions.get('data_registry')
    if not registry:
        return jsonify({'providers': []})

    providers = []
    for item in registry.list_providers():
        provider_name = item['name']
        provider = registry.get_provider(provider_name)

        if provider is not None and hasattr(provider, 'get_rate_limit_status'):
            used, max_, reset_at = provider.get_rate_limit_status()
        else:
            used = 0
            max_ = item.get('rate_limit_per_minute', -1)
            reset_at = None

        providers.append({
            'id': provider_name,
            'display_name': item['display_name'],
            'is_active': item['is_available'],
            'rate_limit_used': used,
            'rate_limit_max': max_,
            'reset_at': reset_at,
        })

    return jsonify({'providers': providers})


@providers_bp.route('/providers/rate-limits', methods=['GET'])
def get_providers_rate_limits():
    """Return rolling-window rate limit state for all registered data providers.

    Reads live in-memory counters from the ``DataProviderRegistry`` and
    computes percentage usage and status buckets for the dashboard panel.

    Returns:
        JSON object::

            {
                "providers": [
                    {
                        "name": "polygon",
                        "display_name": "Polygon.io",
                        "requests_used": 3,
                        "requests_limit": 5,
                        "window_seconds": 60,
                        "reset_at": "2026-02-21T10:31:00Z",
                        "pct_used": 60.0,
                        "status": "ok"
                    }
                ],
                "polled_at": "2026-02-21T10:30:05Z"
            }

    ``status`` values:
        - ``"ok"``       – usage < 70 %
        - ``"warning"``  – 70 % ≤ usage < 90 %
        - ``"critical"`` – usage ≥ 90 %
        - ``"unknown"``  – rate limit ceiling not configured
    """
    registry = current_app.extensions.get('data_registry')
    if not registry:
        return jsonify({
            'providers': [],
            'polled_at': datetime.utcnow().isoformat() + 'Z',
        })

    providers = []
    for item in registry.list_providers():
        provider_name = item['name']
        provider = registry.get_provider(provider_name)

        if provider is not None and hasattr(provider, 'get_rate_limit_status'):
            used, max_, reset_at = provider.get_rate_limit_status()
        else:
            used = 0
            max_ = item.get('rate_limit_per_minute', -1)
            reset_at = None

        if max_ and max_ > 0:
            pct_used = round(used / max_ * 100, 1)
            if pct_used >= 90:
                status = 'critical'
            elif pct_used >= 70:
                status = 'warning'
            else:
                status = 'ok'
        else:
            pct_used = 0.0
            status = 'unknown'

        providers.append({
            'name': provider_name,
            'display_name': item['display_name'],
            'requests_used': used,
            'requests_limit': max_ if max_ and max_ > 0 else None,
            'window_seconds': 60,
            'reset_at': reset_at,
            'pct_used': pct_used,
            'status': status,
        })

    return jsonify({
        'providers': providers,
        'polled_at': datetime.utcnow().isoformat() + 'Z',
    })
