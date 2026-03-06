(Append to existing file)

```python
# ============================================================================
# Earnings API Requests
# ============================================================================

class EarningsFilterRequest(BaseModel):
    """Validation for GET /api/earnings with optional filters."""

    limit: int = Field(default=25, ge=1, le=100, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    status: Optional[str] = Field(None, description="Filter by status: upcoming, reported")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    ticker: Optional[str] = Field(None, max_length=5, description="Filter by ticker")

    VALID_STATUSES: ClassVar[Set[str]] = {'upcoming', 'reported'}

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Ensure status is valid if provided."""
        if v is None:
            return None
        v = v.lower().strip()
        if v not in cls.VALID_STATUSES:
            raise ValueError(f'Status must be one of: {cls.VALID_STATUSES}')
        return v

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
                "limit": 25,
                "offset": 0,
                "status": "upcoming",
                "start_date": "2026-03-01",
                "end_date": "2026-06-30",
                "ticker": "AAPL",
            }
        }


class EarningsSyncRequest(BaseModel):
    """Validation for POST /api/earnings/sync."""

    ticker: Optional[str] = Field(None, max_length=5, description="Ticker to sync (optional, all if null)")
    force_refresh: bool = Field(default=False, description="Force refresh even if recently cached")

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
                "force_refresh": False,
            }
        }
```