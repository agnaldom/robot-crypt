"""
Asset schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    """Base asset schema."""
    symbol: str = Field(..., description="Asset symbol (e.g., BTC/USDT)")
    name: str = Field(..., description="Asset name")
    type: str = Field(..., description="Asset type (crypto, stock, etc.)")
    current_price: Optional[float] = Field(None, description="Current price")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    volume_24h: Optional[float] = Field(None, description="24h trading volume")
    is_active: bool = Field(True, description="Whether asset is active")
    is_monitored: bool = Field(True, description="Whether asset is being monitored")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class AssetCreate(AssetBase):
    """Schema for creating an asset."""
    pass


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    name: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    is_active: Optional[bool] = None
    is_monitored: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class Asset(AssetBase):
    """Schema for asset returned in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
