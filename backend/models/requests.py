```python
"""
Pydantic request validation models for all TickerPulse API endpoints.

These models enforce data validation at the API boundary:
- Type checking
- Range validation
- Required/optional fields
- Automatic error responses on invalid input
"""

from typing import Optional, Dict, Any, ClassVar, Set, List
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Common / Reusable Models
# ============================================================================

class PaginationParams(BaseModel):
    """Standard pagination parameters for list endpoints."""

    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")

    class Config:
        json_schema_extra = {
            "example": {
                "limit": 20,
                "offset": 0,
            }
        }


class ResearchPaginationParams(BaseModel):
    """Pagination for research endpoints (different defaults)."""

    limit: int = Field(default=25, ge=1, le=100, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class AgentPaginationParams(BaseModel):
    """Pagination for agent endpoints (higher limits)."""

    limit: int = Field(default=50, ge=1, le=200, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class SchedulerPaginationParams(BaseModel):
    """Pagination for scheduler endpoints."""

    limit: int = Field(default=50, ge=1, le=200, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


# ============================================================================
# Stock Management
# ============================================================================

class StockCreateRequest(BaseModel):
    """Request to add a stock to monitored list."""

    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker")
    company_name: Optional[str] = Field(None, description="Optional company name")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.upper().strip()
        if not all(c.isalnum() or c in ".-" for c in v):
            raise ValueError("Ticker must contain only alphanumeric characters, dots, and hyphens")
        return v


class StockSearchRequest(BaseModel):
    """Request to search for stocks by ticker or name."""

    q: str = Field(..., min_length=1, description="Search query (ticker or company name)")

    @field_validator("q")
    @classmethod
    def validate_query(cls, v: str) -> str:
        return v.strip()


# ============================================================================
# Watchlist Groups
# ============================================================================

class WatchlistGroupCreateRequest(BaseModel):
    """Request to create a new watchlist group."""

    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")
    color: str = Field(default="#6366f1", regex="^#[0-9a-fA-F]{6}$", description="Hex color code")


class WatchlistGroupUpdateRequest(BaseModel):
    """Request to update a watchlist group."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, regex="^#[0-9a-fA-F]{6}$")


class MoveStockToGroupRequest(BaseModel):
    """Request to move a stock to a different group."""

    group_id: Optional[int] = Field(None, ge=1, description="Target group ID (null to ungroup)")


class ReorderStocksRequest(BaseModel):
    """Request to reorder stocks within a group."""

    stock_ids: List[int] = Field(..., min_length=1, description="Ordered list of stock IDs")


# ============================================================================
# Price Alerts
# ============================================================================

class PriceAlertCreateRequest(BaseModel):
    """Request to create a new price alert."""

    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker")
    alert_type: str = Field(
        ...,
        description="Alert type: above, below, change_percent_up, change_percent_down"
    )
    threshold: float = Field(..., gt=0, description="Price or percentage threshold (> 0)")

    VALID_ALERT_TYPES = {"above", "below", "change_percent_up", "change_percent_down"}

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.upper().strip()
        if not all(c.isalnum() or c in ".-" for c in v):
            raise ValueError("Ticker must contain only alphanumeric characters, dots, and hyphens")
        return v

    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        if v not in cls.VALID_ALERT_TYPES:
            raise ValueError(f"Alert type must be one of: {', '.join(cls.VALID_ALERT_TYPES)}")
        return v

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Threshold must be positive")
        if v > 1000000:
            raise ValueError("Threshold exceeds maximum allowed value")
        return v


class PriceAlertUpdateRequest(BaseModel):
    """Request to update an existing price alert."""

    threshold: Optional[float] = Field(None, gt=0, description="New price or percentage threshold")
    is_active: Optional[bool] = Field(None, description="Enable or disable the alert")

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Threshold must be positive")
        if v is not None and v > 1000000:
            raise ValueError("Threshold exceeds maximum allowed value")
        return v
```