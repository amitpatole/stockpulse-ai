"""
TickerPulse AI v3.0 - Query Parameter Validation Models

Pydantic models for validating GET query parameters.
These models are separate from request body models for better organization.
"""

from typing import Optional, ClassVar, Set
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Pagination Models (Used by multiple endpoints)
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
# Stock Query Parameters
# ============================================================================

class StockListParams(BaseModel):
    """Query parameters for GET /api/stocks."""

    market: Optional[str] = Field(None, description="Filter by market (US, IN, etc)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class StockSearchParams(BaseModel):
    """Query parameters for GET /api/stocks/search."""

    q: str = Field(..., min_length=1, max_length=100, description="Search query")


# ============================================================================
# Research Query Parameters
# ============================================================================

class ResearchBriefsParams(BaseModel):
    """Query parameters for GET /api/research/briefs."""

    ticker: Optional[str] = Field(None, max_length=5, description="Filter by ticker")
    limit: int = Field(default=25, ge=1, le=100, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: Optional[str]) -> Optional[str]:
        """Ensure ticker is uppercase alphanumeric if provided."""
        if v is None:
            return None
        v = v.upper().strip()
        if not v.isalnum():
            raise ValueError('Ticker must be alphanumeric')
        return v


# ============================================================================
# Analysis Query Parameters
# ============================================================================

class RatingsParams(BaseModel):
    """Query parameters for GET /api/ai/ratings."""

    period: int = Field(default=60, ge=1, le=252, description="Days to analyze")
    limit: int = Field(default=50, ge=1, le=1000, description="Max results")


class ChartParams(BaseModel):
    """Query parameters for GET /api/chart/<ticker>."""

    period: str = Field(default='1mo', description="Time period")

    VALID_PERIODS: ClassVar[Set[str]] = {'1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'}

    @field_validator('period')
    @classmethod
    def validate_period(cls, v: str) -> str:
        """Ensure period is one of allowed values."""
        if v not in cls.VALID_PERIODS:
            raise ValueError(f'Period must be one of: {cls.VALID_PERIODS}')
        return v


# ============================================================================
# Agent Query Parameters
# ============================================================================

class AgentListParams(BaseModel):
    """Query parameters for GET /api/agents."""

    category: Optional[str] = Field(None, description="Filter by category")
    enabled: Optional[bool] = Field(None, description="Filter by enabled status")
    limit: int = Field(default=50, ge=1, le=200, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class AgentCostsParams(BaseModel):
    """Query parameters for GET /api/agents/costs."""

    period: str = Field(default='daily', description="Cost period")

    VALID_PERIODS: ClassVar[Set[str]] = {'daily', 'weekly', 'monthly'}

    @field_validator('period')
    @classmethod
    def validate_period(cls, v: str) -> str:
        """Ensure period is valid."""
        if v not in cls.VALID_PERIODS:
            raise ValueError(f'Period must be one of: {cls.VALID_PERIODS}')
        return v


# ============================================================================
# News Query Parameters
# ============================================================================

class NewsParams(BaseModel):
    """Query parameters for GET /api/news."""

    ticker: Optional[str] = Field(None, max_length=5, description="Filter by ticker")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: Optional[str]) -> Optional[str]:
        """Ensure ticker is uppercase alphanumeric if provided."""
        if v is None:
            return None
        v = v.upper().strip()
        if not v.isalnum():
            raise ValueError('Ticker must be alphanumeric')
        return v
