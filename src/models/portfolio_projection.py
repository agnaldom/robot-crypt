from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class PortfolioProjection(Base):
    __tablename__ = "portfolio_projections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)  # Optional, can be for specific portfolio
    
    # Projection configuration
    scenario_type = Column(String, nullable=False)  # optimistic, pessimistic, realistic, custom
    time_horizon = Column(Integer, nullable=False)  # Number of days/months/years
    time_unit = Column(String, nullable=False)  # days, months, years
    
    # Projection inputs
    initial_value = Column(Float, nullable=False)
    expected_return_rate = Column(Float, nullable=False)  # Annualized
    volatility = Column(Float, nullable=False)
    
    # Optional inputs
    recurring_investment = Column(Float, nullable=True)  # Periodic additions
    recurring_frequency = Column(String, nullable=True)  # daily, weekly, monthly
    withdrawal_rate = Column(Float, nullable=True)  # Periodic withdrawals
    inflation_rate = Column(Float, nullable=True)
    
    # Projection results
    projected_value = Column(Float, nullable=False)
    best_case_value = Column(Float, nullable=True)
    worst_case_value = Column(Float, nullable=True)
    
    # Detailed results
    projection_data = Column(JSON, nullable=False)  # Time series data of projections
    
    # Description and notes
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio_projections")
    portfolio = relationship("Portfolio", back_populates="projections")
