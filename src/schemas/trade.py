"""
Trade schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TradeBase(BaseModel):
    """Base trade schema."""
    user_id: Optional[int] = Field(None, description="User ID (optional)")
    asset_id: int = Field(..., description="Asset ID")
    trade_type: str = Field(..., description="Trade type (buy, sell)")
    quantity: float = Field(..., description="Trade quantity")
    price: float = Field(..., description="Trade price")
    total_value: float = Field(..., description="Total trade value")
    fee: float = Field(default=0.0, description="Trading fee")
    status: str = Field(..., description="Trade status (executed, pending, cancelled)")
    notes: Optional[str] = Field(None, description="Trade notes")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class TradeCreate(TradeBase):
    """Schema for creating a trade."""
    pass


class TradeUpdate(BaseModel):
    """Schema for updating a trade."""
    status: Optional[str] = None
    is_profitable: Optional[bool] = None
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Trade(TradeBase):
    """Schema for trade returned in API responses."""
    id: int
    is_profitable: Optional[bool]
    profit_loss: Optional[float]
    profit_loss_percentage: Optional[float]
    executed_at: datetime

    class Config:
        from_attributes = True


class TradeExecution(BaseModel):
    """Schema for trade execution request."""
    asset_symbol: str = Field(..., description="Asset symbol (e.g., BTC/USDT)")
    trade_type: str = Field(..., description="Trade type (buy, sell)")
    quantity: Optional[float] = Field(None, description="Trade quantity (if None, use trade_amount)")
    trade_amount: Optional[float] = Field(None, description="Trade amount in base currency")
    price: Optional[float] = Field(None, description="Limit price (if None, use market price)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")


class TradeSignal(BaseModel):
    """Schema for trade signal."""
    asset_symbol: str = Field(..., description="Asset symbol")
    signal_type: str = Field(..., description="Signal type (buy, sell, hold)")
    strength: float = Field(..., ge=0, le=1, description="Signal strength (0-1)")
    price: float = Field(..., description="Current price")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Technical indicators")
    reasoning: Optional[str] = Field(None, description="Signal reasoning")


class TradePerformance(BaseModel):
    """Schema for trade performance metrics."""
    period: str = Field(..., description="Performance period")
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Win rate percentage")
    total_profit: float = Field(..., description="Total profit/loss")
    total_profit_percentage: float = Field(..., description="Total profit/loss percentage")
    avg_profit_per_trade: float = Field(..., description="Average profit per trade")
    best_trade: float = Field(..., description="Best trade profit")
    worst_trade: float = Field(..., description="Worst trade loss")
    total_fees: float = Field(..., description="Total fees paid")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
