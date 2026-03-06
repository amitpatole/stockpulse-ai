(Append to existing file)

```python
# ============================================================================
# Earnings API Responses
# ============================================================================

class EarningsRecord(BaseModel):
    """Earnings record object in API responses."""

    id: int = Field(..., description="Record ID")
    ticker: str = Field(..., description="Stock ticker")
    earnings_date: str = Field(..., description="Earnings date (YYYY-MM-DD)")
    estimated_eps: Optional[float] = Field(None, description="Estimated EPS")
    actual_eps: Optional[float] = Field(None, description="Actual EPS")
    estimated_revenue: Optional[float] = Field(None, description="Estimated revenue (billions)")
    actual_revenue: Optional[float] = Field(None, description="Actual revenue (billions)")
    surprise_percent: Optional[float] = Field(None, description="EPS surprise percentage")
    fiscal_quarter: Optional[str] = Field(None, description="Fiscal quarter (Q1-Q4)")
    fiscal_year: Optional[int] = Field(None, description="Fiscal year")
    status: str = Field(..., description="Status (upcoming, reported)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ticker": "AAPL",
                "earnings_date": "2026-04-28",
                "estimated_eps": 1.82,
                "actual_eps": 1.95,
                "estimated_revenue": 91.5,
                "actual_revenue": 93.7,
                "surprise_percent": 7.14,
                "fiscal_quarter": "Q2",
                "fiscal_year": 2026,
                "status": "reported",
            }
        }


class EarningsSyncResponse(BaseModel):
    """Response from earnings sync operation."""

    success: bool = Field(..., description="Whether sync succeeded")
    message: str = Field(..., description="Status message")
    count: int = Field(..., description="Number of records synced")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Synced 5 earnings records for AAPL",
                "count": 5,
            }
        }
```