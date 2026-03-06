```python
"""
Pydantic response models for standardized API responses.

Provides:
- Consistent response envelope for all endpoints
- Typed error responses
- Pagination metadata
- Type-safe serialization
"""

from typing import TypeVar, Generic, List, Optional, Any, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field

T = TypeVar('T')


# ============================================================================
# Standard Response Envelopes
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response envelope."""

    success: bool = Field(default=True, description="Always True for success responses")
    message: Optional[str] = Field(None, description="Optional success message")
    data: Optional[Any] = Field(None, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None,
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response for all error cases."""

    error: str = Field(..., description="Error code (machine-readable)")
    message: str = Field(..., description="Error message (human-readable)")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))

    class Config:
        json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Request validation failed",
                "status_code": 400,
                "details": {"field": "error message"},
                "timestamp": "2026-03-06T14:30:00Z"
            }
        }


# ============================================================================
# Pagination
# ============================================================================

class PaginationMeta(BaseModel):
    """Metadata for paginated responses."""

    total: int = Field(..., ge=0, description="Total number of items")
    limit: int = Field(..., ge=1, description="Items per page")
    offset: int = Field(..., ge=0, description="Current offset")
    has_next: bool = Field(..., description="Whether there are more items")
    has_previous: bool = Field(..., description="Whether there are previous items")


# ============================================================================
# Stock Responses
# ============================================================================

class StockResponse(BaseModel):
    """Response for a single stock."""

    id: int
    ticker: str
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    price_change_pct: Optional[float] = None
    market_cap: Optional[str] = None
    active: bool
    group_id: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "current_price": 150.25,
                "price_change_pct": 2.5,
                "market_cap": "2.5T",
                "active": True,
                "group_id": None,
                "created_at": "2026-03-01T10:00:00Z",
                "updated_at": "2026-03-06T14:30:00Z",
            }
        }


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    success: bool = Field(default=True)
    data: Dict[str, Any] = Field(..., description="Paginated data with 'meta' key")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "items": [],
                    "meta": {
                        "total": 0,
                        "limit": 20,
                        "offset": 0,
                        "has_next": False,
                        "has_previous": False,
                    }
                }
            }
        }


# ============================================================================
# Watchlist Group Responses
# ============================================================================

class WatchlistGroupResponse(BaseModel):
    """Response for a watchlist group (list view)."""

    id: int
    name: str
    description: Optional[str] = None
    color: str
    created_at: str
    updated_at: str


class WatchlistGroupDetailResponse(BaseModel):
    """Response for a watchlist group with stocks."""

    id: int
    name: str
    description: Optional[str] = None
    color: str
    stocks: List[StockResponse] = Field(default_factory=list)
    created_at: str
    updated_at: str


# ============================================================================
# Price Alert Responses
# ============================================================================

class PriceAlertResponse(BaseModel):
    """Response for a price alert."""

    id: int
    ticker: str
    alert_type: str
    threshold: float
    is_active: bool
    triggered_count: int
    last_triggered_at: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ticker": "AAPL",
                "alert_type": "above",
                "threshold": 150.00,
                "is_active": True,
                "triggered_count": 2,
                "last_triggered_at": "2026-03-06T14:30:00Z",
                "created_at": "2026-03-01T10:00:00Z",
                "updated_at": "2026-03-06T14:35:00Z",
            }
        }
```