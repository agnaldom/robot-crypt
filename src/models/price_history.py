from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any

from src.database.database import Base


class PriceHistory(Base):
    """SQLAlchemy PriceHistory model for storing OHLCV price data."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_asset_volume = Column(Float, nullable=True)
    number_of_trades = Column(Integer, nullable=True)
    taker_buy_base_volume = Column(Float, nullable=True)
    taker_buy_quote_volume = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    interval = Column(String(10), nullable=False)
    
    # Unique constraint to prevent duplicate records
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'interval', name='price_history_symbol_timestamp_interval_key'),
    )
    
    def __repr__(self):
        return f"<PriceHistory {self.symbol} {self.interval} at {self.timestamp}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'open_time': self.timestamp,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume,
            'quote_asset_volume': self.quote_asset_volume,
            'number_of_trades': self.number_of_trades,
            'taker_buy_base_volume': self.taker_buy_base_volume,
            'taker_buy_quote_volume': self.taker_buy_quote_volume,
            'interval': self.interval
        }
    
    @classmethod
    def from_ohlcv_data(cls, symbol: str, ohlcv_data: Dict[str, Any], interval: str = "1h") -> 'PriceHistory':
        """Create PriceHistory instance from OHLCV data."""
        timestamp = ohlcv_data['open_time']
        if isinstance(timestamp, int):
            timestamp = datetime.fromtimestamp(timestamp / 1000)
        
        return cls(
            symbol=symbol,
            open_price=float(ohlcv_data['open']),
            high_price=float(ohlcv_data['high']),
            low_price=float(ohlcv_data['low']),
            close_price=float(ohlcv_data['close']),
            volume=float(ohlcv_data['volume']),
            quote_asset_volume=float(ohlcv_data.get('quote_asset_volume', 0)),
            number_of_trades=ohlcv_data.get('number_of_trades'),
            taker_buy_base_volume=float(ohlcv_data.get('taker_buy_base_volume', 0)),
            taker_buy_quote_volume=float(ohlcv_data.get('taker_buy_quote_volume', 0)),
            timestamp=timestamp,
            interval=interval
        )
