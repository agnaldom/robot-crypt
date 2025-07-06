from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.database.database import Base


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(str, Enum):
    """Time in force enumeration."""
    GTC = "GTC"  # Good Till Canceled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


@dataclass
class OrderRequest:
    """Order request model."""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    stop_price: Optional[float] = None
    iceberg_quantity: Optional[float] = None
    new_client_order_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data = {
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.type.value,
            "quantity": self.quantity,
            "timeInForce": self.time_in_force.value,
        }
        
        if self.price is not None:
            data["price"] = self.price
        
        if self.stop_price is not None:
            data["stopPrice"] = self.stop_price
        
        if self.iceberg_quantity is not None:
            data["icebergQty"] = self.iceberg_quantity
        
        if self.new_client_order_id is not None:
            data["newClientOrderId"] = self.new_client_order_id
        
        return data


@dataclass
class OrderResponse:
    """Order response model."""
    symbol: str
    order_id: int
    client_order_id: str
    transact_time: datetime
    price: float
    orig_qty: float
    executed_qty: float
    status: OrderStatus
    time_in_force: TimeInForce
    type: OrderType
    side: OrderSide
    
    # Additional fields
    fills: List[Dict[str, Any]] = field(default_factory=list)
    stop_price: Optional[float] = None
    iceberg_qty: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderResponse':
        """Create from API response dictionary."""
        return cls(
            symbol=data["symbol"],
            order_id=data["orderId"],
            client_order_id=data["clientOrderId"],
            transact_time=datetime.fromtimestamp(data["transactTime"] / 1000),
            price=float(data["price"]),
            orig_qty=float(data["origQty"]),
            executed_qty=float(data["executedQty"]),
            status=OrderStatus(data["status"]),
            time_in_force=TimeInForce(data["timeInForce"]),
            type=OrderType(data["type"]),
            side=OrderSide(data["side"]),
            fills=data.get("fills", []),
            stop_price=float(data["stopPrice"]) if "stopPrice" in data else None,
            iceberg_qty=float(data["icebergQty"]) if "icebergQty" in data else None
        )


class Trade(Base):
    """SQLAlchemy Trade model."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    trade_type = Column(String, nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    status = Column(String, nullable=False)  # executed, pending, cancelled
    is_profitable = Column(Boolean, nullable=True)
    profit_loss = Column(Float, nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)
    notes = Column(Text)
    trade_metadata = Column(JSON, default={})
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trades")
    asset = relationship("Asset", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade {self.trade_type} {self.quantity} {self.asset_id} at {self.price}>"
    
    @property
    def net_value(self) -> float:
        """Calculate net value after commission."""
        return self.total_value - self.fee
