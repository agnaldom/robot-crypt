from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from src.database.database import Base


class ReportStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportTypeEnum(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class PortfolioReport(Base):
    """
    Model representing a portfolio report, which contains analysis, metrics,
    and insights about portfolio performance over a specific time period.
    """
    __tablename__ = "portfolio_reports"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportTypeEnum), nullable=False)
    status = Column(Enum(ReportStatusEnum), default=ReportStatusEnum.DRAFT, nullable=False)
    
    # Time period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Report content
    summary = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True)  # Key insights or notable events
    
    # Performance metrics
    total_return = Column(Float, nullable=True)
    annualized_return = Column(Float, nullable=True)
    risk_metrics = Column(JSON, nullable=True)  # Volatility, Sharpe ratio, etc.
    asset_allocation = Column(JSON, nullable=True)  # Current allocation by asset class
    asset_performance = Column(JSON, nullable=True)  # Performance by asset
    
    # Transaction summary
    transaction_summary = Column(JSON, nullable=True)  # Summary of transactions in the period
    
    # Additional sections
    market_analysis = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    custom_sections = Column(JSON, nullable=True)  # For flexible report structure
    
    # Report configuration
    template_id = Column(String(100), nullable=True)  # Reference to a report template
    configuration = Column(JSON, nullable=True)  # Report generation settings
    
    # Report file
    file_path = Column(String(255), nullable=True)  # Path to generated report file (PDF, etc.)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    generated_at = Column(DateTime, nullable=True)  # When the report was last generated
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="reports")
    user = relationship("User", back_populates="portfolio_reports")
    
    def __repr__(self):
        return f"<PortfolioReport {self.title} ({self.report_type}) for Portfolio {self.portfolio_id}>"
