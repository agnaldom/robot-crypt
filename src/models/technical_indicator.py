from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    indicator_type = Column(String, nullable=False)  # RSI, MA, EMA, Bollinger, etc.
    timeframe = Column(String, nullable=False)  # 1h, 4h, 1d, etc.
    value = Column(Float)
    parameters = Column(JSON, default={})  # Period, deviation, etc.
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="technical_indicators")
