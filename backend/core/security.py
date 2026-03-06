
"""
Security utilities for TickerPulse AI v3.0
Handles sensitive data masking, credential protection, and secure logging.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive string, showing only the last N characters.
    
    Args:
        value: The sensitive value (API key, token, password, etc.)
        visible_chars: Number of characters to show at the end (default: 4)
    
    Returns:
        Masked string with asterisks. Example: "sk_live_abc..." → "****...abc"
    
    Examples:
        >>> mask_sensitive_value("example_key_123456789abcdefgh")
        '****...defgh'
        >>> mask_sensitive_value("secret", visible_chars=2)
        '****et'
    """
    if not value:
        return "*" * visible_chars
    
    if len(value) <= visible_chars:
        return "*" * len(value)
    
    masked_part = "*" * (len(value) - visible_chars)
    visible_part = value[-visible_chars:]
    
    # Add ellipsis for values > 15 chars
    if len(value) > 15:
        return f"{masked_part[:3]}...{visible_part}"
    
    return f"{masked_part}{visible_part}"


def mask_api_key_for_logging(api_key: Optional[str]) -> str:
    """
    Mask an API key for safe logging output.
    
    Args:
        api_key: The API key to mask (or None)
    
    Returns:
        Masked API key safe to log, or "[not configured]" if None
    
    Examples:
        >>> mask_api_key_for_logging("example_key_XXXXXXXXXXXXXXXXXXXX")
        'exam...XXXXXX'
    """
    if not api_key:
        return "[not configured]"
    return mask_sensitive_value(api_key, visible_chars=6)


def get_safe_config_dict(config_dict: dict) -> dict:
    """
    Create a safe copy of config dict with sensitive values masked.
    Used for debug logging without exposing credentials.
    
    Args:
        config_dict: Configuration dictionary potentially containing secrets
    
    Returns:
        Copy of dict with masked values for sensitive keys
    
    Example:
        >>> config = {
        ...     'api_key': 'example_key_123456',
        ...     'model': 'gpt-4',
        ...     'secret': 'hunter2'
        ... }
        >>> safe = get_safe_config_dict(config)
        >>> print(safe['api_key'])
        '***...3456'
        >>> print(safe['model'])
        'gpt-4'
    """
    sensitive_keys = {
        'api_key', 'secret_key', 'password', 'token', 'key',
        'api_secret', 'access_token', 'refresh_token',
        'client_secret', 'webhook_secret'
    }
    
    safe_dict = {}
    for key, value in config_dict.items():
        if isinstance(key, str) and any(s in key.lower() for s in sensitive_keys):
            if isinstance(value, str):
                safe_dict[key] = mask_sensitive_value(value)
            else:
                safe_dict[key] = value
        else:
            safe_dict[key] = value
    
    return safe_dict