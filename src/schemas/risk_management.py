"""
Risk management schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class RiskManagementBase(BaseModel):
    """Base risk management schema."""
    asset_id: int = Field(..., description="Asset ID")
    stop_loss_percentage: Optional[float] = Field(None, description="Stop loss percentage")
    take_profit_percentage: Optional[float] = Field(None, description="Take profit percentage")
    max_position_size: Optional[float] = Field(None, description="Maximum position size")
    volatility_index: Optional[float] = Field(None, description="Volatility index")
    risk_level: Optional[str] = Field(None, description="Risk level (low, medium, high)")
    is_active: bool = Field(True, description="Whether risk management is active")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")


class RiskManagementCreate(RiskManagementBase):
    """Schema for creating risk management rule."""
    pass


class RiskManagementUpdate(BaseModel):
    """Schema for updating risk management."""
    stop_loss_percentage: Optional[float] = None
    take_profit_percentage: Optional[float] = None
    max_position_size: Optional[float] = None
    volatility_index: Optional[float] = None
    risk_level: Optional[str] = None
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None


class RiskManagement(RiskManagementBase):
    """Schema for risk management returned in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
