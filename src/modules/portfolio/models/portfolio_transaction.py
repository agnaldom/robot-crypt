from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend_new.core.database import Base


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(String, nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)  # quantity * price
    fee = Column(Float, default=0.0)
    
    # For sell transactions
    realized_profit_loss = Column(Float, nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)
    
    # Additional info
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default={})
    
    # External references
    external_id = Column(String, nullable=True)  # Reference to exchange transaction ID
    external_source = Column(String, nullable=True)  # Exchange or source name
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), nullable=False)  # Actual transaction time
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Record creation time
    
    # Relationships
    user = relationship("User", back_populates="portfolio_transactions")
    asset = relationship("Asset")
