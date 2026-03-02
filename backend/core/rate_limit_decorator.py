"""
TickerPulse AI - Rate Limit Tracking Decorator
Wraps API provider requests to automatically log usage metrics.
"""

import logging
import time
from functools import wraps
from typing import Callable, Any

from backend.core.rate_limit_manager import RateLimitManager

logger = logging.getLogger(__name__)


def track_api_usage(provider_name: str, endpoint: str) -> Callable:
    """
    Decorator to track API calls for rate limit monitoring.
    
    Parameters
    ----------
    provider_name : str
        Name of the provider (CoinGecko, TradingView, SEC)
    endpoint : str
        API endpoint being called
    
    Returns
    -------
    callable
        Decorated function that logs usage metrics
    
    Example
    -------
    @track_api_usage('CoinGecko', '/simple/price')
    async def get_crypto_price(symbol: str):
        # ... API call logic
        return price
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status_code = 500  # Default to error
            
            try:
                result = func(*args, **kwargs)
                status_code = 200  # Success
                return result
            except Exception as e:
                # Determine status code from exception if possible
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    status_code = e.response.status_code
                elif 'rate limit' in str(e).lower() or '429' in str(e):
                    status_code = 429
                else:
                    status_code = 500
                raise
            finally:
                # Log the API call
                response_time_ms = int((time.time() - start_time) * 1000)
                try:
                    RateLimitManager.log_api_call(
                        provider_name=provider_name,
                        endpoint=endpoint,
                        status_code=status_code,
                        response_time_ms=response_time_ms
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log API usage: {log_error}")
        
        return wrapper
    return decorator