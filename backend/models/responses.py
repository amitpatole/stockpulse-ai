(Append to existing file)

```python
# ============================================================================
# Earnings API Responses
# ============================================================================

class EarningsRecord(BaseModel):
    """Earnings record object in API responses."""

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


# =====================================================================
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


# =====================================================================            }
        }
