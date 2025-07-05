from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from backend_new.core.db.base_class import Base


class PortfolioAlert(Base):
    """
    Model representing a portfolio alert, which can be triggered based on
    various conditions like price changes, allocation drift, or risk thresholds.
    """
    __tablename__ = "portfolio_alerts"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Alert details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    alert_type = Column(String(50), nullable=False)  # price, allocation, risk, etc.
    
    # Alert conditions
    condition_type = Column(String(50), nullable=False)  # above, below, change_percent, etc.
    threshold_value = Column(Float, nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)  # Optional, for asset-specific alerts
    
    # Alert status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    
    # Alert configuration
    notification_channels = Column(JSON, nullable=True)  # email, sms, app, etc.
    cooldown_period = Column(Integer, default=86400)  # seconds between repeated alerts
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="alerts")
    asset = relationship("Asset", back_populates="portfolio_alerts", foreign_keys=[asset_id])
    
    def __repr__(self):
        return f"<PortfolioAlert {self.name} ({self.alert_type})>"
