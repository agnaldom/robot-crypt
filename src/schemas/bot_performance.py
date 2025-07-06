"""
Bot performance schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class BotPerformanceBase(BaseModel):
    """Base bot performance schema."""
    period: str = Field(..., description="Period type (daily, weekly, monthly, all_time)")
    total_trades: int = Field(default=0, description="Total number of trades")
    successful_trades: int = Field(default=0, description="Number of successful trades")
    success_rate: float = Field(default=0.0, description="Success rate percentage")
    total_return: float = Field(default=0.0, description="Total return amount")
    return_percentage: float = Field(default=0.0, description="Return percentage")
    current_exposure: float = Field(default=0.0, description="Current market exposure")
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metrics")


class BotPerformanceCreate(BotPerformanceBase):
    """Schema for creating bot performance record."""
    pass


class BotPerformanceUpdate(BaseModel):
    """Schema for updating bot performance."""
    total_trades: Optional[int] = None
    successful_trades: Optional[int] = None
    success_rate: Optional[float] = None
    total_return: Optional[float] = None
    return_percentage: Optional[float] = None
    current_exposure: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None


class BotPerformance(BotPerformanceBase):
    """Schema for bot performance returned in API responses."""
    id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
