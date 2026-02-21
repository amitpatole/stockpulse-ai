"""
TickerPulse AI v3.0 - Data Provider Status API
Exposes per-provider rate limit counters for the Settings UI.
"""

import logging

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
