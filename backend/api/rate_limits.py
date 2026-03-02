"""
TickerPulse AI - Rate Limits API
Endpoints for retrieving API usage and rate limit metrics.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.core.rate_limit_manager import RateLimitManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/rate-limits', tags=['rate-limits'])


@router.get('')
async def get_all_rate_limits() -> Dict:
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
        
        return {
            'data': providers,
            'meta': {
                'total_providers': len(providers),
                'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z'
            },
            'errors': []
        }
    except Exception as e:
        logger.error(f"Failed to get rate limits: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail='Failed to retrieve rate limits'
        )


@router.get('/{provider}/history')
async def get_provider_history(
    provider: str,
    hours: int = Query(24, ge=1, le=720),
    interval: str = Query('hourly', regex='^(hourly|daily)$')
) -> Dict:
    """
    Get historical usage data for a specific provider.
    
    Parameters
    ----------
    provider : str
        Provider name (CoinGecko, TradingView, SEC)
    hours : int
        Number of hours to retrieve (1-720)
    interval : str
        Aggregation interval (hourly or daily)
    
    Returns
    -------
    dict with keys:
        - data: List of hourly/daily usage records
        - meta: Metadata (provider, oldest/newest timestamps, totals)
        - errors: List of errors
    """
    try:
        history = RateLimitManager.get_usage_history(
            provider_name=provider,
            hours=hours,
            interval=interval
        )
        
        if not history:
            return {
                'data': [],
                'meta': {
                    'provider': provider,
                    'oldest_timestamp': None,
                    'newest_timestamp': None,
                    'total_calls': 0,
                    'total_errors': 0
                },
                'errors': []
            }
        
        total_calls = sum(h['call_count'] for h in history)
        total_errors = sum(h['errors'] for h in history)
        
        return {
            'data': history,
            'meta': {
                'provider': provider,
                'oldest_timestamp': history[0]['timestamp'],
                'newest_timestamp': history[-1]['timestamp'],
                'total_calls': total_calls,
                'total_errors': total_errors
            },
            'errors': []
        }
    except Exception as e:
        logger.error(f"Failed to get history for {provider}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail='Failed to retrieve usage history'
        )