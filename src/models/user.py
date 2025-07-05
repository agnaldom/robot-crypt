from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    alerts = relationship("Alert", back_populates="user")
    reports = relationship("Report", back_populates="user")
    
    # Portfolio relationships
    portfolio_snapshots = relationship("PortfolioSnapshot", back_populates="user")
    portfolio_transactions = relationship("PortfolioTransaction", back_populates="user")
    portfolio_metrics = relationship("PortfolioMetric", back_populates="user")
    portfolio_alerts = relationship("PortfolioAlert", back_populates="user")
    portfolio_projections = relationship("PortfolioProjection", back_populates="user")
    portfolio_reports = relationship("PortfolioReport", back_populates="user")
    
    # Legacy relationships (may be removed in future)
    portfolios = relationship("Portfolio", back_populates="owner")
    transactions = relationship("Transaction", back_populates="user")
    risk_profiles = relationship("RiskProfile", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"
