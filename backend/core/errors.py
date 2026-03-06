"""
TickerPulse AI v3.0 - Error Handling & Custom Exceptions

Provides:
- Custom exception classes for different error scenarios
- Error response formatting
- Flask error handlers integration
- Pydantic validation error handling
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from json import JSONDecodeError

from flask import jsonify

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exception Classes
# ============================================================================

class TickerPulseException(Exception):
    """Base exception for all TickerPulse errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize exception with error details.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., "VALIDATION_ERROR")
            status_code: HTTP status code
            details: Additional error context
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to response dictionary."""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        }

    def to_response(self):
        """Convert to Flask response tuple."""
        return jsonify(self.to_dict()), self.status_code


class ValidationError(TickerPulseException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class NotFoundError(TickerPulseException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, resource_type: Optional[str] = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class UnauthorizedError(TickerPulseException):
    """Raised when authentication is required but missing or invalid."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenError(TickerPulseException):
    """Raised when user lacks permission for operation."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
        )


class ConflictError(TickerPulseException):
    """Raised when operation conflicts with existing state."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details,
        )


class RateLimitError(TickerPulseException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class ExternalServiceError(TickerPulseException):
    """Raised when external service (API, DB) fails."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = {}
        if service_name:
            details["service"] = service_name
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=details,
        )


class DatabaseError(TickerPulseException):
    """Raised when database operation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )


# ============================================================================
# Error Response Formatting
# ============================================================================

def format_error_response(
    error: Exception,
    status_code: int = 500,
    error_code: str = "INTERNAL_ERROR",
) -> Dict[str, Any]:
    """
    Format any exception as a standardized error response.

    Args:
        error: Exception that occurred
        status_code: HTTP status code
        error_code: Machine-readable error code

    Returns:
        Dictionary ready to pass to jsonify()
    """
    return {
        "error": error_code,
        "message": str(error),
        "status_code": status_code,
        "details": {},
        "timestamp": datetime.utcnow().isoformat() + 'Z',
    }


def format_validation_errors(validation_errors: list) -> Dict[str, Any]:
    """
    Format Pydantic validation errors into a readable dict.

    Args:
        validation_errors: List from pydantic ValidationError.errors()

    Returns:
        Dictionary mapping field names to error messages
    """
    details = {}
    for error in validation_errors:
        field = '.'.join(str(loc) for loc in error['loc'])
        details[field] = error['msg']
    return details


# ============================================================================
# Flask Error Handlers
# ============================================================================

def register_error_handlers(app) -> None:
    """
    Register Flask error handlers for all custom exceptions.

    Args:
        app: Flask application instance

    Usage:
        from backend.core.errors import register_error_handlers
        app = create_app()
        register_error_handlers(app)
    """

    # TickerPulseException and subclasses
    @app.errorhandler(TickerPulseException)
    def handle_tickerpulse_exception(error: TickerPulseException):
        """Handle custom TickerPulse exceptions."""
        logger.warning(
            f"{error.error_code}: {error.message}",
            extra={"details": error.details},
        )
        return error.to_response()

    # Pydantic validation errors
    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError):
        """Handle Pydantic and other validation errors."""
        logger.warning(f"Validation error: {error}")
        return jsonify(
            format_error_response(
                error,
                status_code=400,
                error_code="VALIDATION_ERROR",
            )
        ), 400

    # JSON decode errors
    @app.errorhandler(JSONDecodeError)
    def handle_json_decode_error(error: JSONDecodeError):
        """Handle malformed JSON requests."""
        logger.warning(f"JSON decode error: {error}")
        return jsonify(
            format_error_response(
                error,
                status_code=400,
                error_code="INVALID_JSON",
            )
        ), 400

    # 404 Not Found
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found."""
        return jsonify(
            format_error_response(
                error,
                status_code=404,
                error_code="NOT_FOUND",
            )
        ), 404

    # 405 Method Not Allowed
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed."""
        return jsonify(
            format_error_response(
                error,
                status_code=405,
                error_code="METHOD_NOT_ALLOWED",
            )
        ), 405

    # 500 Internal Server Error
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error."""
        logger.exception(f"Internal server error: {error}")
        return jsonify(
            format_error_response(
                error,
                status_code=500,
                error_code="INTERNAL_ERROR",
            )
        ), 500

    logger.info("Registered error handlers for TickerPulse exceptions")


# ============================================================================
# Validation Decorator for API Routes
# ============================================================================

from functools import wraps
from flask import request


def validate_json_request(request_model):
    """
    Decorator to validate and parse JSON request bodies.

    Args:
        request_model: Pydantic model class

    Usage:
        from backend.core.errors import validate_json_request
        from backend.models import StockCreateRequest

        @app.post('/api/stocks')
        @validate_json_request(StockCreateRequest)
        def create_stock(data: StockCreateRequest):
            # data is already validated and parsed
            return {}
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                json_data = request.get_json(force=True)
                validated_data = request_model(**json_data)
                return f(*args, data=validated_data, **kwargs)
            except ValueError as e:
                logger.warning(f"Validation error: {e}")
                raise ValidationError(
                    message="Invalid request data",
                    details={"error": str(e)},
                ) from e
            except Exception as e:
                logger.error(f"Request parsing error: {e}")
                raise ValidationError(
                    message="Failed to parse request",
                    details={"error": str(e)},
                ) from e
        return wrapped
    return decorator


def validate_query_params(params_model):
    """
    Decorator to validate and parse query parameters.

    Args:
        params_model: Pydantic model class

    Usage:
        from backend.core.errors import validate_query_params
        from backend.models import PaginationParams

        @app.get('/api/stocks')
        @validate_query_params(PaginationParams)
        def list_stocks(params: PaginationParams):
            # params is already validated and parsed
            return {}
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                validated_data = params_model(**request.args.to_dict())
                return f(*args, params=validated_data, **kwargs)
            except ValueError as e:
                logger.warning(f"Query parameter validation error: {e}")
                raise ValidationError(
                    message="Invalid query parameters",
                    details={"error": str(e)},
                ) from e
            except Exception as e:
                logger.error(f"Query parameter parsing error: {e}")
                raise ValidationError(
                    message="Failed to parse query parameters",
                    details={"error": str(e)},
                ) from e
        return wrapped
    return decorator
