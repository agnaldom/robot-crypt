"""
Trading session schemas for Robot-Crypt application.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

from src.models.trading_session import TradingSessionStatus, TradingStrategy


class TradingSessionBase(BaseModel):
    """Base trading session schema."""
    name: str = Field(..., min_length=1, max_length=255)
    strategy: TradingStrategy
    description: Optional[str] = None
    tags: List[str] = []
    is_simulation: bool = True
    
    # Session configuration
    initial_capital: float = Field(..., gt=0)
    max_drawdown: float = Field(0.2, ge=0, le=1)
    max_daily_loss: float = Field(0.05, ge=0, le=1)
    max_position_size: float = Field(0.1, ge=0, le=1)
    
    # Risk management
    stop_loss_percentage: float = Field(0.02, ge=0, le=1)
    take_profit_percentage: float = Field(0.04, ge=0, le=1)
    risk_per_trade: float = Field(0.01, ge=0, le=1)
    
    # Strategy parameters
    strategy_parameters: Dict[str, Any] = {}


class TradingSessionCreate(TradingSessionBase):
    """Trading session creation schema."""
    pass


class TradingSessionUpdate(BaseModel):
    """Trading session update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[TradingSessionStatus] = None
    
    # Session configuration
    max_drawdown: Optional[float] = Field(None, ge=0, le=1)
    max_daily_loss: Optional[float] = Field(None, ge=0, le=1)
    max_position_size: Optional[float] = Field(None, ge=0, le=1)
    
    # Risk management
    stop_loss_percentage: Optional[float] = Field(None, ge=0, le=1)
    take_profit_percentage: Optional[float] = Field(None, ge=0, le=1)
    risk_per_trade: Optional[float] = Field(None, ge=0, le=1)
    
    # Strategy parameters
    strategy_parameters: Optional[Dict[str, Any]] = None


class TradingSessionResponse(TradingSessionBase):
    """Trading session response schema."""
    id: int
    user_id: int
    status: TradingSessionStatus
    current_capital: float
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit_loss: float = 0.0
    total_fees: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    current_drawdown: float = 0.0
    
    # Calculated metrics
    win_rate: float
    profit_factor: float
    roi: float
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Duration in minutes
    duration_minutes: Optional[int] = None
    
    model_config = ConfigDict(
        from_attributes=True
    )

class TradingSessionSummary(BaseModel):
    """Trading session summary schema."""
    id: int
    name: str
    strategy: TradingStrategy
    status: TradingSessionStatus
    current_capital: float
    total_profit_loss: float
    win_rate: float
    roi: float
    total_trades: int
    created_at: datetime
    is_simulation: bool
    
    model_config = ConfigDict(
        from_attributes=True
    )

class TradingSessionLogCreate(BaseModel):
    """Trading session log creation schema."""
    level: str = Field(..., pattern=r'^(DEBUG|INFO|WARNING|ERROR)$')
    message: str = Field(..., min_length=1)
    event_type: Optional[str] = None
    metadata: Dict[str, Any] = {}


class TradingSessionLogResponse(BaseModel):
    """Trading session log response schema."""
    id: int
    session_id: int
    level: str
    message: str
    event_type: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )

class OpenOrderBase(BaseModel):
    """Base open order schema."""
    asset_id: int
    order_type: str = Field(..., pattern=r'^(market|limit|stop_loss|take_profit)$')
    side: str = Field(..., pattern=r'^(buy|sell)$')
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    
    # Risk management
    stop_loss: Optional[float] = Field(None, gt=0)
    take_profit: Optional[float] = Field(None, gt=0)
    time_in_force: str = Field("GTC", pattern=r'^(GTC|IOC|FOK)$')
    
    # Metadata
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    @field_validator('remaining_quantity', mode='before')
    @classmethod
    def set_remaining_quantity(cls, v, info):
        if v is None:
            return info.data.get('quantity', 0)
        return v


class OpenOrderCreate(OpenOrderBase):
    """Open order creation schema."""
    session_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class OpenOrderUpdate(BaseModel):
    """Open order update schema."""
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)
    take_profit: Optional[float] = Field(None, gt=0)
    time_in_force: Optional[str] = Field(None, pattern=r'^(GTC|IOC|FOK)$')
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class OpenOrderResponse(OpenOrderBase):
    """Open order response schema."""
    id: int
    user_id: int
    session_id: Optional[int] = None
    
    # Order status
    status: str
    filled_quantity: float = 0.0
    remaining_quantity: float
    average_fill_price: Optional[float] = None
    
    # External references
    external_order_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Calculated fields
    fill_percentage: float
    total_value: float
    is_active: bool
    
    model_config = ConfigDict(
        from_attributes=True
    )

class SessionControlRequest(BaseModel):
    """Trading session control request schema."""
    action: str = Field(..., pattern=r'^(start|pause|stop|resume)$')
    reason: Optional[str] = None


class SessionPerformanceMetrics(BaseModel):
    """Trading session performance metrics schema."""
    session_id: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    roi: float
    total_profit_loss: float
    total_fees: float
    max_profit: float
    max_loss: float
    current_drawdown: float
    sharpe_ratio: Optional[float] = None
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    average_win: float = 0.0
    average_loss: float = 0.0
    
    model_config = ConfigDict(
        from_attributes=True
    )

class SessionRiskMetrics(BaseModel):
    """Trading session risk metrics schema."""
    session_id: int
    current_capital: float
    max_drawdown: float
    current_drawdown: float
    risk_per_trade: float
    max_position_size: float
    max_daily_loss: float
    daily_loss: float = 0.0
    var_95: Optional[float] = None  # Value at Risk 95%
    var_99: Optional[float] = None  # Value at Risk 99%
    
    model_config = ConfigDict(
        from_attributes=True
    )

class BulkOrderCreate(BaseModel):
    """Bulk order creation schema."""
    orders: List[OpenOrderCreate] = Field(..., min_items=1, max_items=100)
    session_id: Optional[int] = None
    
    @field_validator('orders')
    @classmethod
    def validate_orders(cls, v):
        if len(v) == 0:
            raise ValueError('At least one order is required')
        return v


class BulkOrderResponse(BaseModel):
    """Bulk order response schema."""
    created_orders: List[OpenOrderResponse] = []
    failed_orders: List[Dict[str, Any]] = []
    total_created: int = 0
    total_failed: int = 0
