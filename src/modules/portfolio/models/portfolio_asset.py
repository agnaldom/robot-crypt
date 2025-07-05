from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend_new.core.database import Base


class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("portfolio_snapshots.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Asset details
    symbol = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    avg_buy_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Asset values
    invested_value = Column(Float, nullable=False)  # quantity * avg_buy_price
    current_value = Column(Float, nullable=False)   # quantity * current_price
    
    # Profit/Loss
    profit_loss = Column(Float, nullable=False)
    profit_loss_percentage = Column(Float, nullable=False)
    
    # Portfolio allocation
    allocation_percentage = Column(Float, nullable=False)  # % of total portfolio
    
    # Asset status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    snapshot = relationship("PortfolioSnapshot", back_populates="assets")
    asset = relationship("Asset", back_populates="portfolio_assets")
