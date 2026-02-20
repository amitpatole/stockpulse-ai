#!/usr/bin/env python3
"""
Shared utility helpers for the backend core package.
"""


def mask_secret(value: str) -> str:
    """Return a masked version of a secret value for safe logging.

    Shows only the last 4 characters for values of 8 or more characters.
    Returns '****' for shorter, empty, or None values.

    Examples:
        mask_secret("sk-abcdef1234") -> "****1234"
        mask_secret("short")         -> "****"
        mask_secret("")              -> "****"
        mask_secret(None)            -> "****"
    """
    if not value or len(value) < 8:
        return "****"
    return f"****{value[-4:]}"
