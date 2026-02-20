"""
Shared utility helpers for the backend.
"""

from __future__ import annotations


def mask_secret(value: str | None) -> str:
    """Return a masked version of a secret, showing only the last 4 characters.

    Examples:
        mask_secret("sk-abcdef1234") -> "****1234"
        mask_secret("ab")            -> "****"
        mask_secret(None)            -> "****"
        mask_secret("")              -> "****"
    """
    if not value or len(value) < 4:
        return "****"
    return f"****{value[-4:]}"
