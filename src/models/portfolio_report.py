from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class PortfolioReport(Base):
    __tablename__ = "portfolio_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report details
    title = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # summary, performance, transactions, tax, custom
    format = Column(String, nullable=False)  # pdf, csv, json
    
    # Time period
    period_type = Column(String, nullable=False)  # daily, weekly, monthly, quarterly, yearly, custom
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Report content
    file_path = Column(String, nullable=True)  # Path to stored report file
    content = Column(Text, nullable=True)  # For small reports stored directly in DB
    parameters = Column(JSON, default={})  # Parameters used to generate the report
    
    # Report status
    is_scheduled = Column(Boolean, default=False)  # Whether this is a scheduled report
    schedule_frequency = Column(String, nullable=True)  # daily, weekly, monthly, quarterly
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio_reports")
