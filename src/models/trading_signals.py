from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

from src.database.database import Base


class TradingSignal(Base):
    """SQLAlchemy TradingSignal model for storing trading signals."""
    __tablename__ = "trading_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL
    strength = Column(Float, nullable=False)  # Signal strength (0-100)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = Column(String(50), nullable=False)  # Source of the signal
    executed = Column(Boolean, server_default='false', nullable=True)
    execution_time = Column(DateTime(timezone=True), nullable=True)
    execution_price = Column(Float, nullable=True)
    execution_success = Column(Boolean, nullable=True)
    reasoning = Column(Text, nullable=True)
    indicators_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<TradingSignal {self.symbol} {self.signal_type} at {self.price}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'strength': self.strength,
            'price': self.price,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source': self.source,
            'executed': self.executed,
            'execution_time': self.execution_time.isoformat() if self.execution_time else None,
            'execution_price': self.execution_price,
            'execution_success': self.execution_success,
            'reasoning': self.reasoning,
            'indicators_data': self.indicators_data,
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def create(cls, symbol: str, signal_type: str, strength: float, price: float, 
               source: str, reasoning: Optional[str] = None, 
               indicators_data: Optional[Dict[str, Any]] = None,
               confidence_score: Optional[float] = None) -> 'TradingSignal':
        """Create TradingSignal instance."""
        return cls(
            symbol=symbol,
            signal_type=signal_type.upper(),
            strength=strength,
            price=price,
            source=source,
            reasoning=reasoning,
            indicators_data=indicators_data,
            confidence_score=confidence_score
        )
