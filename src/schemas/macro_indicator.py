"""
Macro indicator schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class MacroIndicatorBase(BaseModel):
    """Base macro indicator schema."""
    name: str = Field(..., description="Indicator name")
    category: str = Field(..., description="Category (economic_event, index, news, fear_greed)")
    value: Optional[float] = Field(None, description="Indicator value")
    description: Optional[str] = Field(None, description="Description")
    source: Optional[str] = Field(None, description="Data source")
    impact: Optional[str] = Field(None, description="Impact level (high, medium, low)")
    event_date: Optional[datetime] = Field(None, description="Event date")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class MacroIndicatorCreate(MacroIndicatorBase):
    """Schema for creating a macro indicator."""
    pass


class MacroIndicatorUpdate(BaseModel):
    """Schema for updating a macro indicator."""
    value: Optional[float] = None
    description: Optional[str] = None
    impact: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MacroIndicator(MacroIndicatorBase):
    """Schema for macro indicator returned in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
