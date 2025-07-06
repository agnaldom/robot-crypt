"""
Portfolio ORM model for database persistence.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.database import Base


class Portfolio(Base):
    """Portfolio ORM model."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="portfolios")
    alerts = relationship("PortfolioAlert", back_populates="portfolio", cascade="all, delete-orphan")
    assets = relationship("PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", cascade="all, delete-orphan")
    reports = relationship("PortfolioReport", back_populates="portfolio", cascade="all, delete-orphan")
    projections = relationship("PortfolioProjection", back_populates="portfolio", cascade="all, delete-orphan")
    metrics = relationship("PortfolioMetric", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
