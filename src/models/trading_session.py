"""
Trading session model for Robot-Crypt application.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from src.database.database import Base


class TradingSessionStatus(str, enum.Enum):
    """Trading session status enum."""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class TradingStrategy(str, enum.Enum):
    """Trading strategy enum."""
    SCALPING = "scalping"
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    ARBITRAGE = "arbitrage"
    GRID_TRADING = "grid_trading"
    DCA = "dca"  # Dollar Cost Averaging
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    CUSTOM = "custom"


class TradingSession(Base):
    """Trading session model."""
    __tablename__ = "trading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    strategy = Column(SQLEnum(TradingStrategy), nullable=False)
    status = Column(SQLEnum(TradingSessionStatus), default=TradingSessionStatus.ACTIVE)
    
    # Session configuration
    initial_capital = Column(Float, nullable=False)
    current_capital = Column(Float, nullable=False)
    max_drawdown = Column(Float, default=0.2)  # 20% max drawdown
    max_daily_loss = Column(Float, default=0.05)  # 5% max daily loss
    max_position_size = Column(Float, default=0.1)  # 10% max position size
    
    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_profit_loss = Column(Float, default=0.0)
    total_fees = Column(Float, default=0.0)
    max_profit = Column(Float, default=0.0)
    max_loss = Column(Float, default=0.0)
    current_drawdown = Column(Float, default=0.0)
    
    # Risk management
    stop_loss_percentage = Column(Float, default=0.02)  # 2% stop loss
    take_profit_percentage = Column(Float, default=0.04)  # 4% take profit
    risk_per_trade = Column(Float, default=0.01)  # 1% risk per trade
    
    # Strategy parameters
    strategy_parameters = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    
    # Metadata
    description = Column(Text)
    tags = Column(JSON, default=list)
    is_simulation = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="trading_sessions")
    trades = relationship("Trade", back_populates="trading_session")
    session_logs = relationship("TradingSessionLog", back_populates="session")
    
    def __repr__(self):
        return f"<TradingSession(id={self.id}, name='{self.name}', strategy='{self.strategy}', status='{self.status}')>"

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def profit_factor(self) -> float:
        """Calculate profit factor."""
        if self.max_loss == 0:
            return float('inf') if self.max_profit > 0 else 0.0
        return abs(self.max_profit / self.max_loss)

    @property
    def roi(self) -> float:
        """Calculate return on investment percentage."""
        if self.initial_capital == 0:
            return 0.0
        return ((self.current_capital - self.initial_capital) / self.initial_capital) * 100

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == TradingSessionStatus.ACTIVE

    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate session duration in minutes."""
        if not self.started_at:
            return None
        end_time = self.ended_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds() / 60)


class TradingSessionLog(Base):
    """Trading session log model for tracking session events."""
    __tablename__ = "trading_session_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("trading_sessions.id"), nullable=False)
    
    # Log details
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    event_type = Column(String(50))  # trade_executed, signal_generated, error, etc.
    
    # Additional data
    log_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("TradingSession", back_populates="session_logs")
    
    def __repr__(self):
        return f"<TradingSessionLog(id={self.id}, session_id={self.session_id}, level='{self.level}')>"


class OpenOrder(Base):
    """Open order model for tracking pending orders."""
    __tablename__ = "open_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("trading_sessions.id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Order details
    order_type = Column(String(20), nullable=False)  # market, limit, stop_loss, take_profit
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # None for market orders
    stop_price = Column(Float, nullable=True)  # For stop orders
    
    # Order status
    status = Column(String(20), default="pending")  # pending, partial, filled, cancelled
    filled_quantity = Column(Float, default=0.0)
    remaining_quantity = Column(Float, nullable=False)
    average_fill_price = Column(Float, nullable=True)
    
    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    time_in_force = Column(String(10), default="GTC")  # GTC, IOC, FOK
    
    # External references
    external_order_id = Column(String(100), nullable=True)  # Exchange order ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    notes = Column(Text)
    order_metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User")
    session = relationship("TradingSession")
    asset = relationship("Asset")
    
    def __repr__(self):
        return f"<OpenOrder(id={self.id}, side='{self.side}', quantity={self.quantity}, status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in ["pending", "partial"]

    @property
    def fill_percentage(self) -> float:
        """Calculate fill percentage."""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100

    @property
    def total_value(self) -> float:
        """Calculate total order value."""
        price = self.price or 0
        return self.quantity * price
