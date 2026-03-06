"""
TickerPulse AI v3.0 - Request Validation Utilities

Helper functions for validating and parsing API request data.
Works with Pydantic models to provide type-safe request handling.
"""

import logging
from typing import Type, TypeVar, Any, Dict, Optional
from flask import request
from pydantic import BaseModel, ValidationError

from backend.core.errors import ValidationError as TickerPulseValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


def get_request_body(model: Type[T]) -> T:
    """
    Parse and validate JSON request body.

    Args:
        model: Pydantic model to validate against

    Returns:
        Validated model instance

    Raises:
        TickerPulseValidationError: If validation fails

    Example:
        from backend.models import StockCreateRequest
        from backend.core.validation import get_request_body

        @app.post('/api/stocks')
        def create_stock():
            data = get_request_body(StockCreateRequest)
            # data is now validated and typed
            return {"success": True, "ticker": data.ticker}
    """
    try:
        json_data = request.get_json(force=True)
        if json_data is None:
            raise TickerPulseValidationError(
                message="Request body is empty",
                details={"expected": model.__name__},
            )
        return model(**json_data)
    except ValidationError as e:
        details = _format_pydantic_errors(e)
        raise TickerPulseValidationError(
            message=f"Invalid {model.__name__} request",
            details=details,
        ) from e
    except ValueError as e:
        raise TickerPulseValidationError(
            message="Invalid JSON in request body",
            details={"error": str(e)},
        ) from e


def get_query_params(model: Type[T]) -> T:
    """
    Parse and validate query parameters.

    Args:
        model: Pydantic model to validate against

    Returns:
        Validated model instance

    Raises:
        TickerPulseValidationError: If validation fails

    Example:
        from backend.models import PaginationParams
        from backend.core.validation import get_query_params

        @app.get('/api/stocks')
        def list_stocks():
            params = get_query_params(PaginationParams)
            # params.limit and params.offset are validated
            return fetch_stocks(limit=params.limit, offset=params.offset)
    """
    try:
        query_dict = request.args.to_dict()
        # Convert numeric string values to appropriate types
        query_dict = _convert_query_types(query_dict, model)
        return model(**query_dict)
    except ValidationError as e:
        details = _format_pydantic_errors(e)
        raise TickerPulseValidationError(
            message=f"Invalid query parameters for {model.__name__}",
            details=details,
        ) from e
    except ValueError as e:
        raise TickerPulseValidationError(
            message="Invalid query parameter values",
            details={"error": str(e)},
        ) from e


def get_path_param(name: str, expected_type: Type = str) -> Any:
    """
    Get and validate a single path parameter.

    Args:
        name: Parameter name
        expected_type: Expected type (int, str, etc.)

    Returns:
        Validated parameter value

    Raises:
        TickerPulseValidationError: If conversion fails

    Example:
        from backend.core.validation import get_path_param

        @app.get('/api/stocks/<ticker>')
        def get_stock(ticker):
            # ticker is already validated
            return fetch_stock(ticker)
    """
    try:
        view_args = request.view_args or {}
        value = view_args.get(name)
        if value is None:
            raise TickerPulseValidationError(
                message=f"Missing path parameter: {name}",
            )
        if expected_type != str:
            value = expected_type(value)
        return value
    except (ValueError, TypeError) as e:
        view_args = request.view_args or {}
        raise TickerPulseValidationError(
            message=f"Invalid {name} parameter",
            details={
                "expected_type": expected_type.__name__,
                "got": str(view_args.get(name)),
            },
        ) from e


# ============================================================================
# Internal Helpers
# ============================================================================

def _format_pydantic_errors(error: ValidationError) -> Dict[str, Any]:
    """Convert Pydantic ValidationError to readable dict."""
    details = {}
    for err in error.errors():
        field = '.'.join(str(loc) for loc in err['loc'])
        details[field] = err['msg']
    return details


def _convert_query_types(query_dict: Dict[str, str], model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert query string values to appropriate types based on model schema.

    Handles boolean and numeric conversions since all query params come as strings.
    """
    converted = {}
    fields = model.model_fields

    for key, value in query_dict.items():
        if key not in fields:
            # Unknown field - let Pydantic handle it
            converted[key] = value
            continue

        field_info = fields[key]
        field_type = field_info.annotation

        # Handle Optional types
        origin: Any = getattr(field_type, '__origin__', None)
        if origin is not None:
            # Check if it's Optional (Union with None)
            if origin is type(Optional[int]):
                if value.lower() in ('', 'none', 'null'):
                    converted[key] = None
                else:
                    converted[key] = int(value)
                continue
            elif origin is type(Optional[bool]):
                converted[key] = value.lower() in ('true', '1', 'yes', 'on')
                continue

        # Handle non-optional types
        if field_type in (int, float):
            try:
                converted[key] = field_type(value)
            except (ValueError, TypeError):
                converted[key] = value  # Let Pydantic handle the error
        elif field_type is bool:
            converted[key] = value.lower() in ('true', '1', 'yes', 'on')
        else:
            converted[key] = value

    return converted
