"""
Portfolio Position ORM model for simple portfolio API.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class PortfolioPosition(Base):
    """Portfolio Position ORM model."""
    
    __tablename__ = "portfolio_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio_positions")
    
    @property
    def invested_value(self) -> float:
        """Calculate invested value."""
        return self.quantity * self.average_price
    
    @property
    def current_value(self) -> float:
        """Calculate current value."""
        return self.quantity * self.current_price
    
    @property
    def profit_loss(self) -> float:
        """Calculate profit/loss."""
        return self.current_value - self.invested_value
    
    @property
    def profit_loss_percentage(self) -> float:
        """Calculate profit/loss percentage."""
        if self.invested_value == 0:
            return 0.0
        return (self.profit_loss / self.invested_value) * 100
    
    def __repr__(self):
        return f"<PortfolioPosition(id={self.id}, user_id={self.user_id}, symbol='{self.symbol}', quantity={self.quantity})>"
