from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database.database import Base


class PortfolioProjection(Base):
    """
    Model representing a portfolio projection, which contains forecasted portfolio
    values, asset allocations, and risk metrics for future time periods.
    """
    __tablename__ = "portfolio_projections"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Projection metadata
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    projection_type = Column(String(50), nullable=False)  # monte_carlo, trend, scenario, etc.
    
    # Projection parameters
    time_horizon = Column(Integer, nullable=False)  # in days
    confidence_level = Column(Float, default=0.95)
    num_simulations = Column(Integer, default=1000)  # for Monte Carlo simulations
    
    # Projection results
    projected_values = Column(JSON, nullable=False)  # Format: {"timestamp": value, ...}
    projected_returns = Column(JSON, nullable=True)  # Format: {"timestamp": return, ...}
    projected_volatility = Column(JSON, nullable=True)  # Format: {"timestamp": volatility, ...}
    projected_allocations = Column(JSON, nullable=True)  # Format: {"timestamp": {"asset_id": allocation, ...}, ...}
    projected_drawdowns = Column(JSON, nullable=True)  # Format: {"timestamp": drawdown, ...}
    
    # Risk metrics
    worst_case_value = Column(Float, nullable=True)
    best_case_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=False)
    value_at_risk = Column(Float, nullable=True)
    conditional_var = Column(Float, nullable=True)
    
    # Additional data
    assumptions = Column(JSON, nullable=True)  # Assumptions used in the projection
    scenario_data = Column(JSON, nullable=True)  # Additional scenario-specific data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="projections")
    
    def __repr__(self):
        return f"<PortfolioProjection {self.name} for Portfolio {self.portfolio_id}>"
