from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class PortfolioCreateRequest(BaseModel):
    """Request to create a new portfolio."""
    name: str = Field(..., min_length=1, max_length=255, description="Portfolio name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")


class PositionAddRequest(BaseModel):
    """Request to add a position to a portfolio."""
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    quantity: float = Field(..., gt=0, description="Number of shares (must be > 0)")
    cost_basis: float = Field(..., gt=0, description="Cost per share (must be > 0)")


class PositionUpdateRequest(BaseModel):
    """Request to update an existing position."""
    quantity: Optional[float] = Field(None, gt=0, description="Updated quantity")
    cost_basis: Optional[float] = Field(None, gt=0, description="Updated cost basis per share")


class PositionResponse(BaseModel):
    """Response for a single position with calculated P&L metrics."""
    id: int
    ticker: str
    quantity: float
    cost_basis: float
    current_price: float
    total_cost: float  # quantity * cost_basis
    current_value: float  # quantity * current_price
    gain_loss: float  # current_value - total_cost
    gain_loss_percent: float  # (gain_loss / total_cost) * 100
    entry_date: str
    updated_at: str

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    """Response for a portfolio with aggregated metrics and allocation."""
    id: int
    name: str
    description: Optional[str]
    total_cost: float  # Sum of all position costs
    current_value: float  # Sum of all position current values
    total_gain_loss: float  # Sum of all position gains/losses
    total_gain_loss_percent: float  # Weighted portfolio return %
    positions: list[PositionResponse]
    allocation: Dict[str, float]  # {ticker: allocation_percent}
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PortfolioService:
    """Service layer for portfolio calculations and P&L metrics."""

    @staticmethod
    def calculate_position_metrics(
        quantity: float,
        cost_basis: float,
        current_price: float
    ) -> Dict[str, float]:
        """
        Calculate P&L metrics for a single position.
        
        Args:
            quantity: Number of shares held
            cost_basis: Cost per share when purchased
            current_price: Current price per share (from real-time data)
            
        Returns:
            Dict with keys: total_cost, current_value, gain_loss, gain_loss_percent
        """
        total_cost = quantity * cost_basis
        current_value = quantity * current_price
        gain_loss = current_value - total_cost
        gain_loss_percent = (gain_loss / total_cost * 100) if total_cost > 0 else 0.0

        return {
            "total_cost": round(total_cost, 2),
            "current_value": round(current_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_percent": round(gain_loss_percent, 2),
        }

    @staticmethod
    def calculate_allocation(
        positions: list[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate allocation percentages by ticker (for pie chart).
        
        Args:
            positions: List of position dicts with current_value key
            
        Returns:
            Dict mapping {ticker: allocation_percentage}
        """
        total_value = sum(p.get("current_value", 0.0) for p in positions)

        if total_value == 0:
            logger.warning("Total portfolio value is zero; allocation undefined")
            return {}

        allocation = {}
        for pos in positions:
            ticker = pos.get("ticker")
            if ticker:
                percentage = (pos.get("current_value", 0.0) / total_value) * 100
                allocation[ticker] = round(percentage, 2)

        return allocation

    @staticmethod
    def aggregate_portfolio_metrics(
        positions: list[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Aggregate portfolio-level metrics from all positions.
        
        Args:
            positions: List of position dicts with calculated metrics
            
        Returns:
            Dict with portfolio-level totals and percentages
        """
        total_cost = sum(p.get("total_cost", 0.0) for p in positions)
        current_value = sum(p.get("current_value", 0.0) for p in positions)
        total_gain_loss = current_value - total_cost

        total_gain_loss_percent = (
            (total_gain_loss / total_cost * 100) if total_cost > 0 else 0.0
        )

        return {
            "total_cost": round(total_cost, 2),
            "current_value": round(current_value, 2),
            "total_gain_loss": round(total_gain_loss, 2),
            "total_gain_loss_percent": round(total_gain_loss_percent, 2),
        }