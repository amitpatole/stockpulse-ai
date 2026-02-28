```python
"""
TickerPulse AI v3.0 - API Error Handlers
Exception hierarchy and @handle_api_errors decorator for consistent JSON error responses.
"""

import uuid
import logging
import traceback
import functools

from flask import jsonify

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class ApiError(Exception):
    """Base class for all typed API errors."""
    status_code: int = 500
    error_code: str = 'INTERNAL_ERROR'
    retryable: bool = False

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code


class ValidationError(ApiError):
    """400 — client sent invalid or out-of-range input."""
    status_code = 400
    error_code = 'VALIDATION_ERROR'

    def __init__(self, message: str, error_code: str = 'VALIDATION_ERROR'):
        super().__init__(message, error_code)


class NotFoundError(ApiError):
    """404 — requested resource does not exist."""
    status_code = 404
    error_code = 'NOT_FOUND'

    def __init__(self, message: str, error_code: str = 'NOT_FOUND'):
        super().__init__(message, error_code)


class DatabaseError(ApiError):
    """500 — database operation failed."""
    status_code = 500
    error_code = 'DATABASE_ERROR'

    def __init__(self, message: str, error_code: str = 'DATABASE_ERROR'):
        super().__init__(message, error_code)


class ServiceUnavailableError(ApiError):
    """503 — downstream dependency is unavailable. Retryable."""
    status_code = 503
    error_code = 'SERVICE_UNAVAILABLE'
    retryable = True

    def __init__(self, message: str, error_code: str = 'SERVICE_UNAVAILABLE'):
        super().__init__(message, error_code)


class RateLimitError(ApiError):
    """429 — request rate exceeded. Retryable after retry_after seconds."""
    status_code = 429
    error_code = 'RATE_LIMITED'
    retryable = True

    def __init__(self, message: str, retry_after: int = 60, error_code: str = 'RATE_LIMITED'):
        super().__init__(message, error_code)
        self.retry_after = retry_after


class SchedulerJobNotFoundError(ApiError):
    """404 — referenced scheduler job does not exist."""
    status_code = 404
    error_code = 'JOB_NOT_FOUND'

    def __init__(self, message: str, error_code: str = 'JOB_NOT_FOUND'):
        super().__init__(message, error_code)


class SchedulerOperationError(ApiError):
    """500 — scheduler operation failed."""
    status_code = 500
    error_code = 'SCHEDULER_ERROR'

    def __init__(self, message: str, error_code: str = 'SCHEDULER_ERROR'):
        super().__init__(message, error_code)


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def handle_api_errors(func):
    """Catch ApiError subclasses (and bare exceptions) and return JSON error envelopes.

    Successful responses are passed through unchanged.  For ApiError subclasses
    the HTTP status and error_code are taken from the exception.  For any other
    uncaught exception a generic 500 response is returned and the full traceback
    is logged at ERROR level.

    Response shape::

        {
          "success": false,
          "error": "<human-readable message>",
          "error_code": "<SCREAMING_SNAKE_CODE>",
          "retryable": false,
          "request_id": "<short UUID>"
        }

    For RateLimitError a ``Retry-After`` header is also set.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        try:
            return func(*args, **kwargs)
        except ApiError as exc:
            logger.error(
                "API error [%s] HTTP %s: %s | fn=%s",
                exc.error_code,
                exc.status_code,
                exc.message,
                func.__name__,
                exc_info=(exc.status_code >= 500),
            )
            body = {
                'success': False,
                'error': exc.message,
                'error_code': exc.error_code,
                'retryable': exc.retryable,
                'request_id': request_id,
            }
            resp = jsonify(body)
            resp.status_code = exc.status_code
            if isinstance(exc, RateLimitError):
                resp.headers['Retry-After'] = str(exc.retry_after)
            return resp
        except Exception as exc:
            logger.error(
                "Unhandled exception in %s: %s\n%s",
                func.__name__,
                exc,
                traceback.format_exc(),
            )
            body = {
                'success': False,
                'error': 'An internal error occurred',
                'error_code': 'INTERNAL_ERROR',
                'retryable': False,
                'request_id': request_id,
            }
            resp = jsonify(body)
            resp.status_code = 500
            return resp

    return wrapper
```