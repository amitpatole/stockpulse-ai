"""
Input validation for data provider API endpoints.

All validation is done at the API boundary — no changes to DataProviderRegistry
or fallback chain internals. Follows the same pattern established in
backend/api/validators/scheduler_validators.py: regex/allowlist checks,
explicit type checks, and unknown-key rejection.
"""

import re

# ---------------------------------------------------------------------------
# Allowlists
# ---------------------------------------------------------------------------

_ALLOWED_PROVIDER_IDS = frozenset({
    'yahoo_finance',
    'alpha_vantage',
    'finnhub',
    'polygon',
    'newsapi',
})

_ALLOWED_ADD_KEYS = frozenset({'provider_id', 'api_key', 'config'})
_ALLOWED_TEST_KEYS = frozenset({'provider_id', 'api_key'})

# ---------------------------------------------------------------------------
# Field-level patterns
# ---------------------------------------------------------------------------

_API_KEY_RE = re.compile(r'^[A-Za-z0-9_\-]+$')
_API_KEY_MIN = 8
_API_KEY_MAX = 512

_CONFIG_KEY_RE = re.compile(r'^[A-Za-z0-9_]{1,32}$')


# ---------------------------------------------------------------------------
# Field validators
# ---------------------------------------------------------------------------

def validate_provider_id(provider_id):
    """Return ``(True, None)`` when *provider_id* is valid, or ``(False, error_msg)``.

    Checks that the value is a string and is in the explicit allowlist.
    The provider_id value is never reflected in the error message to avoid
    echoing injection payloads back to the caller.
    """
    if not isinstance(provider_id, str):
        return False, (
            "provider_id: must be a string. "
            f"Must be one of: {', '.join(sorted(_ALLOWED_PROVIDER_IDS))}."
        )
    if provider_id not in _ALLOWED_PROVIDER_IDS:
        return False, (
            "provider_id: unrecognised provider. "
            f"Must be one of: {', '.join(sorted(_ALLOWED_PROVIDER_IDS))}."
        )
    return True, None


def validate_api_key(api_key):
    """Return ``(True, None)`` when *api_key* is valid, or ``(False, error_msg)``.

    ``api_key`` is optional at the request level; callers must check for
    presence before calling this helper.
    """
    if not isinstance(api_key, str):
        return False, "api_key: must be a string."
    if not (_API_KEY_MIN <= len(api_key) <= _API_KEY_MAX):
        return False, (
            f"api_key: length must be between {_API_KEY_MIN} and {_API_KEY_MAX} "
            f"characters, got {len(api_key)}."
        )
    if not _API_KEY_RE.match(api_key):
        return False, (
            "api_key: contains invalid characters. "
            "Only letters, digits, underscores, and hyphens are allowed."
        )
    return True, None


def validate_config(config):
    """Return ``(True, None)`` when *config* dict is valid, or ``(False, error_msg)``.

    ``config`` is optional at the request level; callers must check for
    presence before calling this helper.

    Rules:
    - Must be a dict.
    - Keys must match ``^[A-Za-z0-9_]{1,32}$``.
    - Values must be ``str``, ``int``, or ``bool`` (no nested objects or lists).
    """
    if not isinstance(config, dict):
        return False, "config: must be a JSON object (dict)."
    for key, value in config.items():
        if not isinstance(key, str) or not _CONFIG_KEY_RE.match(key):
            return False, (
                f"config: key '{key}' is invalid. "
                "Keys must be 1–32 characters: letters, digits, or underscores only."
            )
        # bool must be checked before int because bool is a subclass of int
        if isinstance(value, bool):
            continue
        if not isinstance(value, (str, int)):
            return False, (
                f"config: value for key '{key}' has unsupported type "
                f"'{type(value).__name__}'. Only str, int, and bool are allowed."
            )
    return True, None


# ---------------------------------------------------------------------------
# Request-level validators
# ---------------------------------------------------------------------------

def validate_add_provider_request(data):
    """Validate the full request body for ``POST /api/settings/data-provider``.

    Args:
        data: Parsed JSON dict from the request body.

    Returns:
        ``(True, None)`` on success, or ``(False, error_message)`` on failure.
    """
    unknown = set(data) - _ALLOWED_ADD_KEYS
    if unknown:
        return False, f"Unknown field(s): {', '.join(sorted(unknown))}."

    ok, err = validate_provider_id(data.get('provider_id'))
    if not ok:
        return False, err

    if 'api_key' in data:
        ok, err = validate_api_key(data['api_key'])
        if not ok:
            return False, err

    if 'config' in data:
        ok, err = validate_config(data['config'])
        if not ok:
            return False, err

    return True, None


def validate_test_provider_request(data):
    """Validate the full request body for ``POST /api/settings/data-provider/test``.

    Args:
        data: Parsed JSON dict from the request body.

    Returns:
        ``(True, None)`` on success, or ``(False, error_message)`` on failure.
    """
    unknown = set(data) - _ALLOWED_TEST_KEYS
    if unknown:
        return False, f"Unknown field(s): {', '.join(sorted(unknown))}."

    ok, err = validate_provider_id(data.get('provider_id'))
    if not ok:
        return False, err

    if 'api_key' in data:
        ok, err = validate_api_key(data['api_key'])
        if not ok:
            return False, err

    return True, None
