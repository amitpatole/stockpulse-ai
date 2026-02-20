#!/usr/bin/env python3
"""Shared utility helpers for backend/core."""

from typing import Optional


def mask_secret(value: Optional[str]) -> str:
    """Return a masked version of a secret for safe logging.

    Shows ``****`` plus the last 4 characters for values >= 8 characters,
    or just ``****`` for shorter/empty/None values.

    Examples::

        mask_secret("sk-abcdef1234")  -> "****1234"
        mask_secret("short")          -> "****"
        mask_secret("")               -> "****"
        mask_secret(None)             -> "****"
    """
    if not value:
        return "****"
    if len(value) >= 8:
        return f"****{value[-4:]}"
    return "****"
