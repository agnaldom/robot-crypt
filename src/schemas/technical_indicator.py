"""
Technical indicator schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TechnicalIndicatorBase(BaseModel):
    """Base technical indicator schema."""
    asset_id: int = Field(..., description="Asset ID")
    indicator_type: str = Field(..., description="Indicator type (RSI, MA, EMA, etc.)")
    timeframe: str = Field(..., description="Timeframe (1h, 4h, 1d, etc.)")
    value: Optional[float] = Field(None, description="Indicator value")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Indicator parameters")


class TechnicalIndicatorCreate(TechnicalIndicatorBase):
    """Schema for creating a technical indicator."""
    pass


class TechnicalIndicatorUpdate(BaseModel):
    """Schema for updating a technical indicator."""
    value: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None


class TechnicalIndicator(TechnicalIndicatorBase):
    """Schema for technical indicator returned in API responses."""
    id: int
    calculated_at: datetime

    class Config:
        from_attributes = True
