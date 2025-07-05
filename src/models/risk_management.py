from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class RiskManagement(Base):
    __tablename__ = "risk_management"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    stop_loss_percentage = Column(Float)
    take_profit_percentage = Column(Float)
    max_position_size = Column(Float)
    volatility_index = Column(Float)
    risk_level = Column(String)  # low, medium, high
    is_active = Column(Boolean, default=True)
    parameters = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="risk_management")
