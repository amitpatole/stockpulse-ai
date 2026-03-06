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
                "error": "VALIDATION_ERROR",
                "message": "Invalid ticker format",
                "status_code": 422,
                "details": {
                    "ticker": "Ticker must be alphanumeric",
                },
                "timestamp": "2026-03-03T12:00:00Z",
            }
        }


# ============================================================================
# Pagination Models
# ============================================================================

class PaginationMeta(BaseModel):
    """Metadata for paginated responses."""

    total: int = Field(..., description="Total items in dataset")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    has_next: bool = Field(..., description="Whether more items exist")
    has_previous: bool = Field(..., description="Whether previous page exists")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "limit": 20,
                "offset": 0,
                "has_next": True,
                "has_previous": False,
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    data: List[T] = Field(..., description="Page of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [],
                "meta": {
                    "total": 150,
                    "limit": 20,
                    "offset": 0,
                    "has_next": True,
                    "has_previous": False,
                },
            }
        }


# ============================================================================
# Watchlist Groups API Responses
# ============================================================================

class WatchlistGroupResponse(BaseModel):
    """Watchlist group object with stock count."""

    id: int = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    color: str = Field(..., description="Hex color code")
    stock_count: int = Field(..., description="Number of stocks in group")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Tech Stocks",
                "description": "My favorite tech companies",
                "color": "#3b82f6",
                "stock_count": 5,
                "created_at": "2026-03-03T12:00:00Z",
                "updated_at": "2026-03-03T12:00:00Z",
            }
        }


class WatchlistGroupDetailResponse(BaseModel):
    """Watchlist group with full stock list."""

    id: int = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    color: str = Field(..., description="Hex color code")
    stocks: List[str] = Field(..., description="List of tickers in order")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Tech Stocks",
                "description": "My favorite tech companies",
                "color": "#3b82f6",
                "stocks": ["AAPL", "MSFT", "GOOGL"],
                "created_at": "2026-03-03T12:00:00Z",
                "updated_at": "2026-03-03T12:00:00Z",
            }
        }


# ============================================================================
# Stock API Responses
# ============================================================================

class StockResponse(BaseModel):
    """Stock object in API responses."""

    ticker: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    market: str = Field(..., description="Market (US, IN, etc)")
    active: bool = Field(default=True, description="Whether stock is in watchlist")
    group_id: Optional[int] = Field(None, description="Watchlist group ID")
    created_at: Optional[str] = Field(None, description="When added to watchlist")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "US",
                "active": True,
                "group_id": 1,
                "created_at": "2026-03-03T12:00:00Z",
                "updated_at": "2026-03-03T12:00:00Z",
            }
        }


class StockCreateResponse(BaseModel):
    """Response from creating a stock."""

    success: bool = Field(..., description="Whether operation succeeded")
    ticker: str = Field(..., description="Stock ticker")
    name: Optional[str] = Field(None, description="Stock name")
    market: Optional[str] = Field(None, description="Market")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "US",
            }
        }


class StockDeleteResponse(BaseModel):
    """Response from deleting a stock."""

    success: bool = Field(..., description="Whether deletion succeeded")
    ticker: Optional[str] = Field(None, description="Deleted ticker")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticker": "AAPL",
            }
        }


# ============================================================================
# Research API Responses
# ============================================================================

class ResearchBriefResponse(BaseModel):
    """Research brief object in API responses."""

    id: int = Field(..., description="Brief ID")
    ticker: str = Field(..., description="Stock ticker")
    title: str = Field(..., description="Brief title")
    content: str = Field(..., description="Brief content")
    agent_name: str = Field(..., description="Agent that generated this")
    model_used: str = Field(..., description="Model used for generation")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ticker": "AAPL",
                "title": "Apple Inc. Market Analysis",
                "content": "...",
                "agent_name": "sentiment_analyst",
                "model_used": "claude-haiku",
                "created_at": "2026-03-03T12:00:00Z",
            }
        }


# ============================================================================
# Analysis API Responses
# ============================================================================

class RatingResponse(BaseModel):
    """Stock rating object."""

    ticker: str = Field(..., description="Stock symbol")
    rating: str = Field(..., description="Rating (BUY, HOLD, SELL)")
    score: float = Field(..., description="Numerical score")
    confidence: float = Field(..., description="Confidence level (0-1)")
    rsi: Optional[float] = Field(None, description="RSI value")
    sentiment_score: Optional[float] = Field(None, description="Sentiment (-1 to 1)")
    technical_score: Optional[float] = Field(None, description="Technical score")
    fundamental_score: Optional[float] = Field(None, description="Fundamental score")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "rating": "BUY",
                "score": 8.5,
                "confidence": 0.92,
                "rsi": 65.3,
                "sentiment_score": 0.75,
                "technical_score": 0.8,
                "fundamental_score": 0.85,
            }
        }


class ChartDataPoint(BaseModel):
    """Single OHLCV candle."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")


class ChartResponse(BaseModel):
    """Historical price data response."""

    ticker: str = Field(..., description="Stock symbol")
    period: str = Field(..., description="Time period")
    data: List[ChartDataPoint] = Field(..., description="OHLCV data points")
    currency_symbol: str = Field(..., description="Currency symbol")
    stats: Optional[Dict[str, float]] = Field(None, description="Statistics (min, max, avg)")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "period": "1mo",
                "data": [
                    {
                        "date": "2026-02-03",
                        "open": 200.0,
                        "high": 205.0,
                        "low": 198.0,
                        "close": 202.5,
                        "volume": 50000000,
                    }
                ],
                "currency_symbol": "$",
                "stats": {"min": 198.0, "max": 205.0, "avg": 201.25},
            }
        }


# ============================================================================
# Agents API Responses
# ============================================================================

class AgentResponse(BaseModel):
    """Agent object in API responses."""

    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role")
    goal: str = Field(..., description="Agent goal")
    backstory: str = Field(..., description="Agent backstory")
    model: str = Field(..., description="Model name")
    provider: str = Field(..., description="AI provider")
    enabled: bool = Field(..., description="Whether agent is enabled")
    tags: List[str] = Field(default_factory=list, description="Agent tags")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "sentiment_analyst",
                "role": "Market Sentiment Analyst",
                "goal": "Analyze market sentiment",
                "backstory": "...",
                "model": "claude-haiku-4-5-20251001",
                "provider": "anthropic",
                "enabled": True,
                "tags": ["analysis", "sentiment"],
            }
        }


class AgentRunResponse(BaseModel):
    """Response from running an agent."""

    success: bool = Field(..., description="Whether run succeeded")
    run_id: str = Field(..., description="Run ID for tracking")
    agent: str = Field(..., description="Agent name")
    status: str = Field(..., description="Run status")
    duration_ms: int = Field(..., description="Execution time in ms")
    completed_at: str = Field(..., description="Completion timestamp")
    output: Optional[str] = Field(None, description="Agent output")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "run_id": "run_123abc",
                "agent": "sentiment_analyst",
                "status": "success",
                "duration_ms": 5000,
                "completed_at": "2026-03-03T12:00:00Z",
                "output": "Analysis results...",
            }
        }


# ============================================================================
# Chat API Responses
# ============================================================================

class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    success: bool = Field(..., description="Whether request succeeded")
    ticker: str = Field(..., description="Stock ticker")
    question: str = Field(..., description="User's question")
    answer: str = Field(..., description="AI's answer")
    ai_powered: bool = Field(..., description="Whether AI was used")
    thinking_level: Optional[str] = Field(None, description="Thinking level used")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticker": "AAPL",
                "question": "What is the technical outlook?",
                "answer": "Based on current technical analysis...",
                "ai_powered": True,
                "thinking_level": "balanced",
            }
        }


# ============================================================================
# Settings API Responses
# ============================================================================

class ProviderConfig(BaseModel):
    """AI provider configuration."""

    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    configured: bool = Field(..., description="Whether it's configured")
    models: List[str] = Field(..., description="Available models")
    default_model: Optional[str] = Field(None, description="Default model")
    is_active: bool = Field(..., description="Whether it's currently active")
    status: str = Field(..., description="Status (configured, not_configured, error)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "anthropic",
                "display_name": "Anthropic",
                "configured": True,
                "models": ["claude-haiku", "claude-sonnet"],
                "default_model": "claude-haiku",
                "is_active": True,
                "status": "configured",
            }
        }


class SettingsResponse(BaseModel):
    """Response from settings operations."""

    success: bool = Field(..., description="Whether operation succeeded")
    message: Optional[str] = Field(None, description="Status message")
    provider: Optional[str] = Field(None, description="Provider name")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Settings updated",
                "provider": "anthropic",
            }
        }


# ============================================================================
# News API Responses
# ============================================================================

class NewsArticle(BaseModel):
    """News article object."""

    id: int = Field(..., description="Article ID")
    ticker: str = Field(..., description="Stock ticker")
    title: str = Field(..., description="Article title")
    description: Optional[str] = Field(None, description="Article summary")
    url: Optional[str] = Field(None, description="Article URL")
    source: Optional[str] = Field(None, description="News source")
    published_date: Optional[str] = Field(None, description="Publication date")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    sentiment_label: Optional[str] = Field(None, description="Sentiment label")
    created_at: str = Field(..., description="When added to DB")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ticker": "AAPL",
                "title": "Apple Reports Strong Q4 Results",
                "description": "...",
                "url": "https://...",
                "source": "Reuters",
                "published_date": "2026-03-03",
                "sentiment_score": 0.8,
                "sentiment_label": "positive",
                "created_at": "2026-03-03T12:00:00Z",
            }
        }


class StockStats(BaseModel):
    """Stock statistics from news."""

    ticker: str = Field(..., description="Stock ticker")
    total_articles: int = Field(..., description="Total articles")
    positive_count: int = Field(..., description="Positive articles")
    negative_count: int = Field(..., description="Negative articles")
    neutral_count: int = Field(..., description="Neutral articles")
    avg_sentiment: float = Field(..., description="Average sentiment score")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "total_articles": 25,
                "positive_count": 15,
                "negative_count": 5,
                "neutral_count": 5,
                "avg_sentiment": 0.65,
            }
        }


# ============================================================================
# Scheduler API Responses
# ============================================================================

class SchedulerJobResponse(BaseModel):
    """Scheduler job object."""

    job_id: str = Field(..., description="Job ID")
    name: str = Field(..., description="Job name")
    status: str = Field(..., description="Job status")
    next_run_time: Optional[str] = Field(None, description="Next scheduled run")
    last_run_time: Optional[str] = Field(None, description="Last run time")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "daily_indicators",
                "name": "Daily Indicators Update",
                "status": "running",
                "next_run_time": "2026-03-04T09:00:00Z",
                "last_run_time": "2026-03-03T09:00:00Z",
            }
        }


class SchedulerOperationResponse(BaseModel):
    """Response from scheduler operations."""

    success: bool = Field(..., description="Whether operation succeeded")
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="New status")
    message: Optional[str] = Field(None, description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "job_id": "daily_indicators",
                "status": "paused",
                "message": "Job paused successfully",
            }
        }
```