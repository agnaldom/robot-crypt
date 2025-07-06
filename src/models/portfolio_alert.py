from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class PortfolioAlert(Base):
    __tablename__ = "portfolio_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)  # Optional, can be for entire portfolio
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)  # Optional, can be for entire portfolio
    
    # Alert configuration
    alert_type = Column(String, nullable=False)  # price, value, percentage, risk
    alert_level = Column(String, nullable=False)  # info, warning, danger
    
    # Alert conditions
    condition_type = Column(String, nullable=False)  # above, below, equals
    threshold_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)  # Current value being monitored
    
    # Alert content
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert status
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    
    # Notification preferences
    notify_email = Column(Boolean, default=True)
    notify_push = Column(Boolean, default=True)
    notify_in_app = Column(Boolean, default=True)
    
    # Advanced configuration
    recurrence = Column(String, nullable=True)  # once, hourly, daily, weekly
    cool_down_minutes = Column(Integer, default=0)  # Minutes before re-triggering
    additional_config = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="portfolio_alerts")
    portfolio = relationship("Portfolio", back_populates="alerts")
    asset = relationship("Asset", back_populates="portfolio_alerts")
