from sqlalchemy import Column, Integer, Float, DateTime, JSON, ForeignKey, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    
    # Portfolio totals
    total_invested_value = Column(Float, nullable=False)
    current_market_value = Column(Float, nullable=False)
    total_profit_loss = Column(Float, nullable=False)
    profit_loss_percentage = Column(Float, nullable=False)
    
    # Risk metrics
    risk_level = Column(String, nullable=True)  # low, medium, high
    value_at_risk = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    # Additional metrics
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Benchmark comparisons (as percentage differences)
    btc_comparison = Column(Float, nullable=True)  # Performance relative to BTC
    eth_comparison = Column(Float, nullable=True)  # Performance relative to ETH
    
    # JSON field for additional metrics and flexibility
    metrics = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio_snapshots")
    portfolio = relationship("Portfolio", back_populates="snapshots")
    assets = relationship("PortfolioAsset", back_populates="snapshot", cascade="all, delete-orphan")
