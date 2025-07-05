from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # performance, trade_history, risk_analysis
    format = Column(String, nullable=False)  # pdf, csv, json
    content = Column(Text, nullable=True)  # For small reports or links
    parameters = Column(JSON, default={})
    file_path = Column(String, nullable=True)  # For stored files
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reports")
