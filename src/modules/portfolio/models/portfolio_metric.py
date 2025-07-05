from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend_new.database.base import Base


class PortfolioMetric(Base):
    __tablename__ = "portfolio_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time period
    period_type = Column(String, nullable=False)  # daily, weekly, monthly, yearly, all_time
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Performance metrics
    starting_value = Column(Float, nullable=False)
    ending_value = Column(Float, nullable=False)
    absolute_return = Column(Float, nullable=False)  # Ending - Starting
    percentage_return = Column(Float, nullable=False)  # (Ending - Starting) / Starting
    
    # Risk metrics
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    value_at_risk = Column(Float, nullable=True)
    
    # Benchmark comparison
    btc_return = Column(Float, nullable=True)  # BTC return for same period
    eth_return = Column(Float, nullable=True)  # ETH return for same period
    market_return = Column(Float, nullable=True)  # Overall crypto market return
    
    # Additional metrics
    average_win = Column(Float, nullable=True)
    average_loss = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)  # Percentage of profitable trades
    additional_metrics = Column(JSON, default={})
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio_metrics")
