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
# Watchlist Groups API Requests
# ============================================================================

class WatchlistGroupCreateRequest(BaseModel):
    """Validation for POST /api/watchlist-groups (create group)."""

    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")
    color: Optional[str] = Field(None, regex=r'^#[0-9a-f]{6}$', description="Hex color code")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError('Group name cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tech Stocks",
                "description": "My favorite tech companies",
                "color": "#3b82f6",
            }
        }


class WatchlistGroupUpdateRequest(BaseModel):
    """Validation for PUT /api/watchlist-groups/{id}."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")
    color: Optional[str] = Field(None, regex=r'^#[0-9a-f]{6}$', description="Hex color code")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Ensure name is not just whitespace."""
        if v is None:
            return None
        if not v.strip():
            raise ValueError('Group name cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Tech",
                "color": "#8b5cf6",
            }
        }


class MoveStockToGroupRequest(BaseModel):
    """Validation for POST /api/stocks/{ticker}/group."""

    group_id: Optional[int] = Field(None, description="Group ID (null to move to 'All')")

    class Config:
        json_schema_extra = {
            "example": {
                "group_id": 1,
            }
        }


class ReorderStocksRequest(BaseModel):
    """Validation for PUT /api/watchlist-groups/{id}/stocks."""

    ticker_order: List[str] = Field(..., description="Ordered list of tickers in the group")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker_order": ["AAPL", "MSFT", "GOOGL"],
            }
        }


# ============================================================================
# Stock API Requests
# ============================================================================

class StockCreateRequest(BaseModel):
    """Validation for POST /api/stocks (add stock to watchlist)."""

    ticker: str = Field(..., min_length=1, max_length=5, description="Stock symbol")
    name: Optional[str] = Field(None, max_length=255, description="Company name")
    market: Optional[str] = Field(None, description="Market (US, IN, etc)")

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Ensure ticker is uppercase alphanumeric."""
        v = v.upper().strip()
        if not v.isalnum():
            raise ValueError('Ticker must be alphanumeric')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "US",
            }
        }


class StockSearchRequest(BaseModel):
    """Validation for GET /api/stocks/search."""

    q: str = Field(..., min_length=1, max_length=100, description="Search query")

    class Config:
        json_schema_extra = {
            "example": {
                "q": "Apple",
            }
        }


# ============================================================================
# Research API Requests
# ============================================================================

class ResearchBriefRequest(BaseModel):
    """Validation for POST /api/research/briefs."""

    ticker: Optional[str] = Field(None, max_length=5, description="Stock ticker (optional)")

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

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
            }
        }


# ============================================================================
# Analysis API Requests
# ============================================================================

class RatingsRequest(BaseModel):
    """Validation for GET /api/ai/ratings."""

    period: int = Field(default=60, ge=1, le=252, description="Days to analyze")
    limit: int = Field(default=50, ge=1, le=1000, description="Max results")

    class Config:
        json_schema_extra = {
            "example": {
                "period": 60,
                "limit": 50,
            }
        }


class ChartRequest(BaseModel):
    """Validation for GET /api/chart/<ticker>."""

    period: str = Field(default='1mo', description="Time period")

    VALID_PERIODS: ClassVar[Set[str]] = {'1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'}

    @field_validator('period')
    @classmethod
    def validate_period(cls, v: str) -> str:
        """Ensure period is one of allowed values."""
        if v not in cls.VALID_PERIODS:
            raise ValueError(f'Period must be one of: {cls.VALID_PERIODS}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "period": "1mo",
            }
        }


# ============================================================================
# Agents API Requests
# ============================================================================

class AgentRunRequest(BaseModel):
    """Validation for POST /api/agents/<name>/run."""

    params: Optional[Dict[str, Any]] = Field(default=None, description="Agent parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "params": {
                    "ticker": "AAPL",
                    "depth": "detailed",
                }
            }
        }


class AgentFiltersRequest(BaseModel):
    """Validation for GET /api/agents with optional filters."""

    category: Optional[str] = Field(None, description="Agent category")
    enabled: Optional[bool] = Field(None, description="Filter by enabled status")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "analysis",
                "enabled": True,
            }
        }


class AgentCostsRequest(BaseModel):
    """Validation for GET /api/agents/costs."""

    period: str = Field(default='daily', description="Cost period")

    VALID_PERIODS: ClassVar[Set[str]] = {'daily', 'weekly', 'monthly'}

    @field_validator('period')
    @classmethod
    def validate_period(cls, v: str) -> str:
        """Ensure period is valid."""
        if v not in cls.VALID_PERIODS:
            raise ValueError(f'Period must be one of: {cls.VALID_PERIODS}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "period": "daily",
            }
        }


# ============================================================================
# Chat API Requests
# ============================================================================

class ChatRequest(BaseModel):
    """Validation for POST /api/chat/ask."""

    ticker: str = Field(..., min_length=1, max_length=5, description="Stock symbol")
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    thinking_level: Optional[str] = Field(
        default='balanced',
        description="Response depth: quick, balanced, deep"
    )

    VALID_THINKING_LEVELS: ClassVar[Set[str]] = {'quick', 'balanced', 'deep'}

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Ensure ticker is uppercase alphanumeric."""
        v = v.upper().strip()
        if not v.isalnum():
            raise ValueError('Ticker must be alphanumeric')
        return v

    @field_validator('thinking_level')
    @classmethod
    def validate_thinking_level(cls, v: Optional[str]) -> Optional[str]:
        """Ensure thinking level is valid."""
        if v is None:
            return 'balanced'
        if v not in cls.VALID_THINKING_LEVELS:
            raise ValueError(f'Thinking level must be one of: {cls.VALID_THINKING_LEVELS}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "question": "What is the current technical outlook?",
                "thinking_level": "balanced",
            }
        }


# ============================================================================
# Settings API Requests
# ============================================================================

class SettingsRequest(BaseModel):
    """Validation for POST /api/settings/ai-provider."""

    provider: str = Field(..., description="AI provider name")
    api_key: str = Field(..., min_length=1, description="API key or credentials")
    model: Optional[str] = Field(None, description="Model name (optional)")

    VALID_PROVIDERS: ClassVar[Set[str]] = {'anthropic', 'openai', 'google_ai', 'xai'}

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Ensure provider is recognized."""
        v = v.lower().strip()
        if v not in cls.VALID_PROVIDERS:
            raise ValueError(f'Provider must be one of: {cls.VALID_PROVIDERS}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "anthropic",
                "api_key": "sk-ant-...",
                "model": "claude-haiku-4-5-20251001",
            }
        }


class DataProviderRequest(BaseModel):
    """Validation for POST /api/settings/data-provider."""

    provider_id: str = Field(..., description="Data provider ID")
    api_key: Optional[str] = Field(None, description="API key if required")
    config: Optional[Dict[str, Any]] = Field(None, description="Provider-specific config")

    class Config:
        json_schema_extra = {
            "example": {
                "provider_id": "yahoo_finance",
                "api_key": None,
                "config": {},
            }
        }


class AgentFrameworkRequest(BaseModel):
    """Validation for POST /api/settings/agent-framework."""

    framework: str = Field(..., description="Framework name")

    VALID_FRAMEWORKS: ClassVar[Set[str]] = {'crewai', 'openclaw'}

    @field_validator('framework')
    @classmethod
    def validate_framework(cls, v: str) -> str:
        """Ensure framework is recognized."""
        v = v.lower().strip()
        if v not in cls.VALID_FRAMEWORKS:
            raise ValueError(f'Framework must be one of: {cls.VALID_FRAMEWORKS}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "framework": "crewai",
            }
        }


# ============================================================================
# News API Requests
# ============================================================================

class NewsRequest(BaseModel):
    """Validation for GET /api/news."""

    ticker: Optional[str] = Field(None, max_length=5, description="Filter by ticker")

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

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
            }
        }


# ============================================================================
# Scheduler API Requests
# ============================================================================

class SchedulerJobRequest(BaseModel):
    """Validation for PUT /api/scheduler/jobs/<job_id>/schedule."""

    trigger: str = Field(..., description="Trigger type: cron, interval, date")

    # Cron trigger fields
    cron_expression: Optional[str] = Field(None, description="Cron expression (for trigger='cron')")
    timezone: Optional[str] = Field(None, description="Timezone for cron")

    # Interval trigger fields
    interval_seconds: Optional[int] = Field(None, ge=1, description="Interval in seconds")

    # Date trigger fields
    run_date: Optional[str] = Field(None, description="Date to run (ISO format)")

    VALID_TRIGGERS: ClassVar[Set[str]] = {'cron', 'interval', 'date'}

    @field_validator('trigger')
    @classmethod
    def validate_trigger(cls, v: str) -> str:
        """Ensure trigger is valid."""
        v = v.lower().strip()
        if v not in cls.VALID_TRIGGERS:
            raise ValueError(f'Trigger must be one of: {cls.VALID_TRIGGERS}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "trigger": "cron",
                "cron_expression": "0 9 * * *",
                "timezone": "US/Eastern",
            }
        }
```