from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    alert_type = Column(String, nullable=False)  # price, technical, macro, risk
    message = Column(Text, nullable=False)
    trigger_value = Column(Float)
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    parameters = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    asset = relationship("Asset", back_populates="alerts")
