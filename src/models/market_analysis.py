from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any

from src.database.database import Base


class MarketAnalysis(Base):
    """SQLAlchemy MarketAnalysis model for storing market analysis data."""
    __tablename__ = "market_analysis"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    
    @classmethod
    async def save_analysis(cls, session, symbol, analysis_type, data):
        """Salva análise no banco de dados"""
        try:
            new_analysis = cls.create(symbol, analysis_type, data)
            session.add(new_analysis)
            # Não fazemos commit aqui - deixamos para o context manager
            # await session.commit()
            return new_analysis
        except Exception as e:
            await session.rollback()
            raise

    def __repr__(self):
        return f"<MarketAnalysis {self.symbol} {self.analysis_type} at {self.created_at}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'analysis_type': self.analysis_type,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create(cls, symbol: str, analysis_type: str, data: Dict[str, Any]) -> 'MarketAnalysis':
        """Create MarketAnalysis instance."""
        return cls(
            symbol=symbol,
            analysis_type=analysis_type,
            data=data
        )
