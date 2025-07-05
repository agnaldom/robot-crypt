from typing import Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from backend_new.core.db.base_class import Base


class User(Base):
    """
    User model for authentication and authorization
    """
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - add as needed for your application
    # portfolios = relationship("Portfolio", back_populates="owner")
    # alerts = relationship("Alert", back_populates="user")
    # reports = relationship("Report", back_populates="user")
