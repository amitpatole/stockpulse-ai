def mask_secret(value: str) -> str:
    """Return masked version of a secret — last 4 chars only."""
    if value and len(value) >= 8:
        return f"****{value[-4:]}"
    return "****"
