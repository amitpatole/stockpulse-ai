```python
"""
Price alerts API endpoints - CRUD operations and notifications.
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

from backend.core.alert_manager import (
    create_price_alert, get_price_alert, list_price_alerts,
    update_price_alert, delete_price_alert
)
from backend.core.validation import get_request_body, get_query_params
from backend.core.errors import NotFoundError, ValidationError as TickerPulseValidationError
from backend.models.requests import (
    PriceAlertCreateRequest, PriceAlertUpdateRequest, PaginationParams
)

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api')


@alerts_bp.route('/price-alerts', methods=['GET'])
def list_alerts() -> tuple[Dict[str, Any], int]:
    """List all price alerts with pagination and filters.

    Query Parameters (validated by PaginationParams):
        limit (int, optional): Items per page. Range: 1-100, Default: 20
        offset (int, optional): Pagination offset. Default: 0

    Query Parameters (custom):
        ticker (string, optional): Filter by ticker
        active_only (boolean, optional): Show only active alerts

    Response 200:
    {
      "success": true,
      "data": {
        "alerts": [...],
        "meta": {...}
      }
    }
    """
    try:
        # Validate pagination params
        params = get_query_params(request, PaginationParams)
        ticker = request.args.get('ticker', '').upper() or None
        active_only = request.args.get('active_only', 'false').lower() == 'true'

        result = list_price_alerts(
            limit=params.limit,
            offset=params.offset,
            ticker=ticker,
            active_only=active_only,
        )

        return {
            'success': True,
            'data': result,
        }, 200

    except TickerPulseValidationError as e:
        return {
            'error': 'validation_error',
            'message': str(e),
            'status_code': 400,
        }, 400
    except Exception as e:
        logger.error(f"Error listing price alerts: {e}", exc_info=True)
        return {
            'error': 'internal_error',
            'message': 'Failed to list price alerts',
            'status_code': 500,
        }, 500


@alerts_bp.route('/price-alerts', methods=['POST'])
def create_alert() -> tuple[Dict[str, Any], int]:
    """Create a new price alert.

    Request Body:
    {
      "ticker": "AAPL",
      "alert_type": "above",
      "threshold": 150.00
    }

    Response 201:
    {
      "success": true,
      "message": "Price alert created",
      "data": {...}
    }
    """
    try:
        body = get_request_body(request, PriceAlertCreateRequest)
        alert = create_price_alert(body)

        return {
            'success': True,
            'message': 'Price alert created',
            'data': alert.model_dump(),
        }, 201

    except TickerPulseValidationError as e:
        return {
            'error': 'validation_error',
            'message': str(e),
            'status_code': 400,
        }, 400
    except Exception as e:
        logger.error(f"Error creating price alert: {e}", exc_info=True)
        return {
            'error': 'internal_error',
            'message': 'Failed to create price alert',
            'status_code': 500,
        }, 500


@alerts_bp.route('/price-alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id: int) -> tuple[Dict[str, Any], int]:
    """Get a specific price alert by ID.

    Response 200:
    {
      "success": true,
      "data": {...}
    }
    """
    try:
        alert = get_price_alert(alert_id)
        return {
            'success': True,
            'data': alert.model_dump(),
        }, 200

    except NotFoundError as e:
        return {
            'error': 'not_found',
            'message': str(e),
            'status_code': 404,
        }, 404
    except Exception as e:
        logger.error(f"Error getting price alert: {e}", exc_info=True)
        return {
            'error': 'internal_error',
            'message': 'Failed to get price alert',
            'status_code': 500,
        }, 500


@alerts_bp.route('/price-alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id: int) -> tuple[Dict[str, Any], int]:
    """Update an existing price alert.

    Request Body (all fields optional):
    {
      "threshold": 155.00,
      "is_active": false
    }

    Response 200:
    {
      "success": true,
      "message": "Price alert updated",
      "data": {...}
    }
    """
    try:
        body = get_request_body(request, PriceAlertUpdateRequest)
        alert = update_price_alert(alert_id, body)

        return {
            'success': True,
            'message': 'Price alert updated',
            'data': alert.model_dump(),
        }, 200

    except NotFoundError as e:
        return {
            'error': 'not_found',
            'message': str(e),
            'status_code': 404,
        }, 404
    except TickerPulseValidationError as e:
        return {
            'error': 'validation_error',
            'message': str(e),
            'status_code': 400,
        }, 400
    except Exception as e:
        logger.error(f"Error updating price alert: {e}", exc_info=True)
        return {
            'error': 'internal_error',
            'message': 'Failed to update price alert',
            'status_code': 500,
        }, 500


@alerts_bp.route('/price-alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id: int) -> tuple[Dict[str, Any], int]:
    """Delete a price alert.

    Response 200:
    {
      "success": true,
      "message": "Price alert deleted"
    }
    """
    try:
        delete_price_alert(alert_id)

        return {
            'success': True,
            'message': 'Price alert deleted',
        }, 200

    except NotFoundError as e:
        return {
            'error': 'not_found',
            'message': str(e),
            'status_code': 404,
        }, 404
    except Exception as e:
        logger.error(f"Error deleting price alert: {e}", exc_info=True)
        return {
            'error': 'internal_error',
            'message': 'Failed to delete price alert',
            'status_code': 500,
        }, 500
```