from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # crypto, stock, etc.
    current_price = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    is_active = Column(Boolean, default=True)
    is_monitored = Column(Boolean, default=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    technical_indicators = relationship("TechnicalIndicator", back_populates="asset")
    trades = relationship("Trade", back_populates="asset")
    risk_management = relationship("RiskManagement", back_populates="asset")
    alerts = relationship("Alert", back_populates="asset")
    
    # Portfolio relationships
    portfolio_assets = relationship("PortfolioAsset", back_populates="asset")
    portfolio_alerts = relationship("PortfolioAlert", back_populates="asset")
