"""
TickerPulse AI v3.0 - Pydantic Models for Request/Response Validation

This package provides:
- Request validation models (Pydantic v2)
- Response models for consistency
- Error response models
- Type-safe API contracts

Usage:
    from backend.models import PaginationParams, StockResponse

    @app.get('/api/stocks')
    def list_stocks(params: PaginationParams):
        # params is auto-validated and parsed
        ...
"""

from backend.models.requests import (
    PaginationParams,
    StockCreateRequest,
    StockSearchRequest,
    ResearchBriefRequest,
    AgentRunRequest,
    ChatRequest,
    SettingsRequest,
    SchedulerJobRequest,
    NewsRequest,
)

from backend.models.responses import (
    PaginatedResponse,
    StockResponse,
    ResearchBriefResponse,
    AgentResponse,
    AgentRunResponse,
    ErrorResponse,
    SuccessResponse,
)

__all__ = [
    # Requests
    'PaginationParams',
    'StockCreateRequest',
    'StockSearchRequest',
    'ResearchBriefRequest',
    'AgentRunRequest',
    'ChatRequest',
    'SettingsRequest',
    'SchedulerJobRequest',
    'NewsRequest',
    # Responses
    'PaginatedResponse',
    'StockResponse',
    'ResearchBriefResponse',
    'AgentResponse',
    'AgentRunResponse',
    'ErrorResponse',
    'SuccessResponse',
]
