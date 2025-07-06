from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime
from sqlalchemy.sql import func

from src.database.database import Base


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # Economic event, index, news, fear_greed
    value = Column(Float)
    description = Column(Text)
    source = Column(String)
    impact = Column(String)  # high, medium, low
    event_date = Column(DateTime(timezone=True))
    indicator_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
