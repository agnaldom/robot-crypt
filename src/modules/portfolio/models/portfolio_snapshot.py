from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Snapshot timestamp
    snapshot_date = Column(DateTime(timezone=True), nullable=False)
    
    # Portfolio values
    total_value = Column(Float, nullable=False)
    total_invested = Column(Float, nullable=False)
    total_profit_loss = Column(Float, nullable=False)
    total_profit_loss_percentage = Column(Float, nullable=False)
    
    # Portfolio metrics
    daily_change = Column(Float, nullable=True)
    daily_change_percentage = Column(Float, nullable=True)
    weekly_change = Column(Float, nullable=True)
    weekly_change_percentage = Column(Float, nullable=True)
    monthly_change = Column(Float, nullable=True)
    monthly_change_percentage = Column(Float, nullable=True)
    
    # Risk metrics
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    var_95 = Column(Float, nullable=True)  # Value at Risk (95%)
    
    # Snapshot status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio_snapshots")
    assets = relationship("PortfolioAsset", back_populates="snapshot", cascade="all, delete-orphan")
    
    def __str__(self):
        return f"Portfolio Snapshot {self.id} - {self.snapshot_date} - Total: {self.total_value}"
