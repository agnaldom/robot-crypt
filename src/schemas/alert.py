"""
Alert schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    """Base alert schema."""
    user_id: int = Field(..., description="User ID")
    asset_id: Optional[int] = Field(None, description="Asset ID (optional)")
    alert_type: str = Field(..., description="Alert type (price, technical, macro, risk)")
    message: str = Field(..., description="Alert message")
    trigger_value: Optional[float] = Field(None, description="Trigger value")
    is_active: bool = Field(True, description="Whether alert is active")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Alert parameters")


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    pass


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    alert_type: Optional[str] = None
    message: Optional[str] = None
    trigger_value: Optional[float] = None
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None


class Alert(AlertBase):
    """Schema for alert returned in API responses."""
    id: int
    is_triggered: bool
    created_at: datetime
    triggered_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertTrigger(BaseModel):
    """Schema for triggering an alert."""
    alert_id: int = Field(..., description="Alert ID")
    current_value: Optional[float] = Field(None, description="Current value that triggered alert")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional trigger data")
