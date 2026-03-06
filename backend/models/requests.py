# ============================================================================
# Earnings API Requests
# ============================================================================

class EarningsFilterRequest(BaseModel):
    """Validation for GET /api/earnings with optional filters."""

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


# =====================================================================```