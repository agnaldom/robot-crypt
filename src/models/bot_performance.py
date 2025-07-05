from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.sql import func

from src.database.database import Base


class BotPerformance(Base):
    __tablename__ = "bot_performance"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String, nullable=False)  # daily, weekly, monthly, all_time
    total_trades = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    return_percentage = Column(Float, default=0.0)
    current_exposure = Column(Float, default=0.0)
    metrics = Column(JSON, default={})  # Additional metrics like Sharpe ratio, drawdown, etc.
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
