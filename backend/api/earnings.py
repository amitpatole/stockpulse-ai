```python
"""
TickerPulse AI v3.0 - Earnings Calendar API Routes
Blueprint for earnings calendar endpoints: list, filter, and sync.

Input Validation:
- All inputs validated using Pydantic models in backend.models.requests
- Validation errors return 422 with details on invalid fields
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import sqlite3

from backend.core.validation import get_request_body, get_query_params
from backend.core.errors import NotFoundError, ValidationError as TickerPulseValidationError
from backend.database import get_db_connection, db_session
from backend.models.requests import (
    EarningsFilterRequest, EarningsSyncRequest
)
from backend.models.responses import (
    PaginatedResponse, EarningsRecord, PaginationMeta, EarningsSyncResponse
)

logger = logging.getLogger(__name__)

earnings_bp = Blueprint('earnings', __name__, url_prefix='/api')


# ============================================================================
# Earnings Endpoints
# ============================================================================

@earnings_bp.route('/earnings', methods=['GET'])
def get_earnings() -> tuple[Dict[str, Any], int]:
    """Get paginated earnings records with filtering.

    Query Parameters (validated by EarningsFilterRequest):
        limit (int, optional): Items per page. Range: 1-100, Default: 25
        offset (int, optional): Pagination offset. Default: 0
        status (str, optional): Filter by status: upcoming, reported
        start_date (str, optional): ISO date (YYYY-MM-DD)
        end_date (str, optional): ISO date (YYYY-MM-DD)
        ticker (str, optional): Filter by ticker

    Returns:
        tuple[Dict[str, Any], int]: (response_body, status_code)
    """
    try:
        # Validate query parameters
        params = get_query_params(request, EarningsFilterRequest)

        with db_session() as conn:
            # Build query with filters
            query = "SELECT * FROM earnings_calendar WHERE 1=1"
            args = []

            if params.status:
                query += " AND status = ?"
                args.append(params.status)

            if params.ticker:
                query += " AND ticker = ?"
                args.append(params.ticker)

            if params.start_date:
                query += " AND earnings_date >= ?"
                args.append(params.start_date)

            if params.end_date:
                query += " AND earnings_date <= ?"
                args.append(params.end_date)

            # Get total count
            count_query = query.replace(
                "SELECT *", "SELECT COUNT(*) as count"
            )
            cursor = conn.execute(count_query, args)
            total = cursor.fetchone()['count']

            # Get paginated results
            query += " ORDER BY earnings_date DESC LIMIT ? OFFSET ?"
            args.extend([params.limit, params.offset])

            cursor = conn.execute(query, args)
            rows = cursor.fetchall()

            # Convert rows to EarningsRecord objects
            earnings_data = [
                EarningsRecord(
                    id=row['id'],
                    ticker=row['ticker'],
                    earnings_date=row['earnings_date'],
                    estimated_eps=row['estimated_eps'],
                    actual_eps=row['actual_eps'],
                    estimated_revenue=row['estimated_revenue'],
                    actual_revenue=row['actual_revenue'],
                    surprise_percent=row['surprise_percent'],
                    fiscal_quarter=row['fiscal_quarter'],
                    fiscal_year=row['fiscal_year'],
                    status=row['status'],
                )
                for row in rows
            ]

            # Build response
            has_next = params.offset + params.limit < total
            has_previous = params.offset > 0

            response_data = {
                "data": [item.model_dump() for item in earnings_data],
                "meta": {
                    "total": total,
                    "limit": params.limit,
                    "offset": params.offset,
                    "has_next": has_next,
                    "has_previous": has_previous,
                }
            }

            return jsonify(response_data), 200

    except TickerPulseValidationError as e:
        return jsonify({"error": "VALIDATION_ERROR", "message": str(e)}), 422
    except Exception as e:
        logger.error(f"Error fetching earnings: {e}")
        return jsonify({"error": "INTERNAL_ERROR", "message": "Failed to fetch earnings"}), 500


@earnings_bp.route('/earnings/<ticker>', methods=['GET'])
def get_earnings_by_ticker(ticker: str) -> tuple[Dict[str, Any], int]:
    """Get earnings history for a specific ticker.

    Path Parameters:
        ticker (str): Stock ticker symbol

    Query Parameters:
        limit (int, optional): Items per page. Default: 25
        offset (int, optional): Pagination offset. Default: 0

    Returns:
        tuple[Dict[str, Any], int]: (response_body, status_code)
    """
    try:
        # Validate ticker
        ticker = ticker.upper().strip()
        if not ticker.isalnum():
            raise TickerPulseValidationError("Ticker must be alphanumeric")

        # Get pagination params
        limit = request.args.get('limit', 25, type=int)
        offset = request.args.get('offset', 0, type=int)

        if limit < 1 or limit > 100:
            limit = 25
        if offset < 0:
            offset = 0

        with db_session() as conn:
            # Get total count for this ticker
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM earnings_calendar WHERE ticker = ?",
                [ticker]
            )
            total = cursor.fetchone()['count']

            if total == 0:
                # Return empty result
                response_data = {
                    "data": [],
                    "meta": {
                        "total": 0,
                        "limit": limit,
                        "offset": offset,
                        "has_next": False,
                        "has_previous": False,
                    }
                }
                return jsonify(response_data), 200

            # Get paginated results
            cursor = conn.execute(
                """
                SELECT * FROM earnings_calendar 
                WHERE ticker = ? 
                ORDER BY earnings_date DESC 
                LIMIT ? OFFSET ?
                """,
                [ticker, limit, offset]
            )
            rows = cursor.fetchall()

            # Convert to EarningsRecord objects
            earnings_data = [
                EarningsRecord(
                    id=row['id'],
                    ticker=row['ticker'],
                    earnings_date=row['earnings_date'],
                    estimated_eps=row['estimated_eps'],
                    actual_eps=row['actual_eps'],
                    estimated_revenue=row['estimated_revenue'],
                    actual_revenue=row['actual_revenue'],
                    surprise_percent=row['surprise_percent'],
                    fiscal_quarter=row['fiscal_quarter'],
                    fiscal_year=row['fiscal_year'],
                    status=row['status'],
                )
                for row in rows
            ]

            has_next = offset + limit < total
            has_previous = offset > 0

            response_data = {
                "data": [item.model_dump() for item in earnings_data],
                "meta": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_next": has_next,
                    "has_previous": has_previous,
                }
            }

            return jsonify(response_data), 200

    except TickerPulseValidationError as e:
        return jsonify({"error": "VALIDATION_ERROR", "message": str(e)}), 422
    except Exception as e:
        logger.error(f"Error fetching earnings for {ticker}: {e}")
        return jsonify({"error": "INTERNAL_ERROR", "message": "Failed to fetch earnings"}), 500


@earnings_bp.route('/earnings/sync', methods=['POST'])
def sync_earnings() -> tuple[Dict[str, Any], int]:
    """Sync earnings data from external source (admin endpoint).

    Request Body:
        {
            "ticker": "AAPL" (optional),
            "force_refresh": false
        }

    Returns:
        tuple[Dict[str, Any], int]: (response_body, status_code)
    """
    try:
        # Validate request body
        body = get_request_body(request, EarningsSyncRequest)

        # TODO: Implement actual sync from external data source
        # For now, return placeholder response
        count = 0
        ticker_str = body.ticker or "all stocks"

        response = EarningsSyncResponse(
            success=True,
            message=f"Synced {count} earnings records for {ticker_str}",
            count=count
        )

        return jsonify(response.model_dump()), 200

    except TickerPulseValidationError as e:
        return jsonify({"error": "VALIDATION_ERROR", "message": str(e)}), 422
    except Exception as e:
        logger.error(f"Error syncing earnings: {e}")
        return jsonify({"error": "INTERNAL_ERROR", "message": "Failed to sync earnings"}), 500
```